"""seed_db.py — loads the synthetic CSV dataset into the database."""
import sqlite3
import pandas as pd
from pathlib import Path
from database import get_db, init_db

CSV_PATH = Path(__file__).parent.parent / "data" / "refound_dataset.csv"

# Auto-generated secret Q/A for seeded found reports.
# (In the real app, finders type their own when submitting.)
SECRET_QA = {
    "Electronics":     ("What brand or model is it?",        "see description"),
    "Wallet/ID":       ("What name is on the card inside?",  "Mohamed Khoucham"),
    "Keys":            ("What is attached to the keyring?",  "see description"),
    "Bag":             ("What is inside the bag?",           "see description"),
    "Clothing":        ("What size is it?",                  "medium"),
    "Jewellery":       ("Describe the engraving or pendant", "see description"),
    "Books/Documents": ("What name is written inside?",      "Mohamed Khoucham"),
    "Other":           ("Describe a unique detail",          "see description"),
}


def seed():
    init_db()
    df = pd.read_csv(CSV_PATH).fillna({"match_id": ""})
    conn = get_db()
    inserted = 0
    for _, r in df.iterrows():
        q, a = (SECRET_QA[r.category] if r.report_type == "found" else (None, None))
        try:
            conn.execute(
                """INSERT INTO reports
                   (report_type, category, description, location,
                    date_reported, secret_question, secret_answer, contact_email)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (r.report_type, r.category, r.description, r.location,
                 r.date_reported, q, a, "seed@refound.test"),
            )
            inserted += 1
        except sqlite3.IntegrityError as e:
            print("Skipped one row:", e)
    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    conn.close()
    print(f"Inserted {inserted} rows. Table now has {total} reports.")


if __name__ == "__main__":
    seed()