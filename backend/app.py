"""app.py — ReFound REST API."""
from flask import Flask, request, jsonify
from flask_cors import CORS
from database import get_db, init_db
from ml.matcher import Matcher
from ml.classifier import load_model, suggest_category
from ml.verifier import check_answer

app = Flask(__name__)
CORS(app)  # lets the frontend (a different port) call this API

MAX_VERIFY_ATTEMPTS = 3

# ---- load ML once at startup ----
init_db()
matcher = Matcher()
classifier = load_model()


def refit_matcher():
    """Re-learn TF-IDF vocabulary from every description in the DB."""
    conn = get_db()
    rows = conn.execute("SELECT description FROM reports").fetchall()
    conn.close()
    if rows:
        matcher.fit([r["description"] for r in rows])


refit_matcher()


# ---------------- Reports ----------------

@app.route("/api/reports", methods=["POST"])
def create_report():
    d = request.get_json()
    required = ["report_type", "category", "description", "contact_email"]
    missing = [f for f in required if not d.get(f)]
    if missing:
        return jsonify(error=f"Missing fields: {missing}"), 400
    if d["report_type"] not in ("lost", "found"):
        return jsonify(error="report_type must be 'lost' or 'found'"), 400

    conn = get_db()
    cur = conn.execute(
        """INSERT INTO reports (report_type, category, description, location,
           date_reported, photo_url, secret_question, secret_answer, contact_email)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (d["report_type"], d["category"], d["description"], d.get("location"),
         d.get("date_reported"), d.get("photo_url"),
         d.get("secret_question"), d.get("secret_answer"), d["contact_email"]))
    report_id = cur.lastrowid
    conn.commit()
    conn.close()

    refit_matcher()                       # new words may have appeared
    matches = compute_matches(report_id)  # auto-match on submission
    return jsonify(id=report_id, matches=matches), 201


@app.route("/api/reports", methods=["GET"])
def list_reports():
    q = ("SELECT id, report_type, category, description, location, "
         "date_reported, photo_url, status FROM reports WHERE 1=1")
    params = []
    if request.args.get("type"):
        q += " AND report_type = ?"
        params.append(request.args["type"])
    if request.args.get("category"):
        q += " AND category = ?"
        params.append(request.args["category"])
    if request.args.get("search"):
        q += " AND description LIKE ?"
        params.append(f"%{request.args['search']}%")
    q += " ORDER BY id DESC"
    conn = get_db()
    rows = [dict(r) for r in conn.execute(q, params).fetchall()]
    conn.close()
    return jsonify(rows)


@app.route("/api/reports/<int:rid>", methods=["GET"])
def get_report(rid):
    conn = get_db()
    row = conn.execute(
        "SELECT id, report_type, category, description, location, "
        "date_reported, photo_url, status FROM reports WHERE id = ?",
        (rid,)).fetchone()
    conn.close()
    if not row:
        return jsonify(error="Report not found"), 404
    return jsonify(dict(row))


# ---------------- Matching ----------------

def compute_matches(report_id, k=3):
    """Find top-k opposite-type, same-category reports and store them."""
    conn = get_db()
    rep = conn.execute("SELECT * FROM reports WHERE id = ?",
                       (report_id,)).fetchone()
    opposite = "found" if rep["report_type"] == "lost" else "lost"
    cands = [dict(r) for r in conn.execute(
        "SELECT id, description, category, location, photo_url FROM reports "
        "WHERE report_type = ? AND category = ? AND status = 'open' AND id != ?",
        (opposite, rep["category"], report_id)).fetchall()]

    top = matcher.top_matches(rep["description"], cands, k=k)

    for m in top:  # store; lost always on the left
        lost_id = report_id if rep["report_type"] == "lost" else m["id"]
        found_id = m["id"] if rep["report_type"] == "lost" else report_id
        conn.execute(
            """INSERT OR IGNORE INTO matches
               (lost_report_id, found_report_id, similarity_score)
               VALUES (?,?,?)""", (lost_id, found_id, m["similarity"]))
    conn.commit()
    conn.close()
    return top


@app.route("/api/reports/<int:rid>/matches", methods=["GET"])
def get_matches(rid):
    return jsonify(compute_matches(rid))


# ---------------- Category suggestion ----------------

@app.route("/api/suggest-category", methods=["POST"])
def api_suggest_category():
    desc = (request.get_json() or {}).get("description", "")
    if len(desc.split()) < 3:
        return jsonify(error="Description too short to classify"), 400
    cat, conf = suggest_category(classifier, desc)
    return jsonify(category=cat, confidence=conf)


# ---------------- Verification ----------------

@app.route("/api/verify", methods=["POST"])
def verify():
    """Body: {lost_report_id, found_report_id, answer}"""
    d = request.get_json()
    conn = get_db()
    match = conn.execute(
        "SELECT * FROM matches WHERE lost_report_id = ? AND found_report_id = ?",
        (d["lost_report_id"], d["found_report_id"])).fetchone()
    if not match:
        conn.close()
        return jsonify(error="No such match"), 404

    attempts = conn.execute(
        "SELECT COUNT(*) FROM verifications WHERE match_id = ?",
        (match["id"],)).fetchone()[0]
    if attempts >= MAX_VERIFY_ATTEMPTS:
        conn.close()
        return jsonify(error="Attempt limit reached"), 403

    found = conn.execute("SELECT * FROM reports WHERE id = ?",
                         (d["found_report_id"],)).fetchone()
    passed, score = check_answer(d.get("answer", ""), found["secret_answer"] or "")

    conn.execute(
        "INSERT INTO verifications (match_id, submitted_answer, fuzzy_score, passed) "
        "VALUES (?,?,?,?)",
        (match["id"], d.get("answer", ""), score, int(passed)))
    if passed:
        conn.execute("UPDATE matches SET status='confirmed' WHERE id=?",
                     (match["id"],))
        conn.execute("UPDATE reports SET status='matched' WHERE id IN (?,?)",
                     (d["lost_report_id"], d["found_report_id"]))
    conn.commit()

    resp = {"passed": passed, "score": score,
            "attempts_left": MAX_VERIFY_ATTEMPTS - attempts - 1}
    if passed:
        resp["contact_email"] = found["contact_email"]  # the reveal!
    conn.close()
    return jsonify(resp)


@app.route("/api/reports/<int:rid>/question", methods=["GET"])
def get_question(rid):
    conn = get_db()
    row = conn.execute("SELECT secret_question FROM reports WHERE id = ?",
                       (rid,)).fetchone()
    conn.close()
    if not row or not row["secret_question"]:
        return jsonify(error="No secret question on this report"), 404
    return jsonify(secret_question=row["secret_question"])


if __name__ == "__main__":
    app.run(debug=True)