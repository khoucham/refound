"""database.py — creates and connects to the SQLite database."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "refound.db"


def get_db():
    """Open a connection. Rows behave like dictionaries (row['column_name'])."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reports (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER REFERENCES users(id),
    report_type     TEXT NOT NULL CHECK (report_type IN ('lost','found')),
    category        TEXT NOT NULL,
    description     TEXT NOT NULL,
    location        TEXT,
    date_reported   TEXT,
    photo_url       TEXT,
    secret_question TEXT,
    secret_answer   TEXT,
    contact_email   TEXT,
    status          TEXT DEFAULT 'open' CHECK (status IN ('open','matched','closed'))
);

CREATE TABLE IF NOT EXISTS matches (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    lost_report_id   INTEGER NOT NULL REFERENCES reports(id),
    found_report_id  INTEGER NOT NULL REFERENCES reports(id),
    similarity_score REAL NOT NULL,
    status           TEXT DEFAULT 'suggested'
                     CHECK (status IN ('suggested','confirmed','rejected')),
    created_at       TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (lost_report_id, found_report_id)
);

CREATE TABLE IF NOT EXISTS verifications (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id         INTEGER NOT NULL REFERENCES matches(id),
    submitted_answer TEXT NOT NULL,
    fuzzy_score      REAL NOT NULL,
    passed           INTEGER NOT NULL,
    attempted_at     TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def init_db():
    conn = get_db()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    print(f"Database ready at {DB_PATH}")


if __name__ == "__main__":
    init_db()