"""
database.py
============
Lightweight SQLite persistence layer.

What problem this solves
-------------------------
A CSV-based prototype can't represent "this opportunity was added last
week, updated yesterday, and expires in 3 days" - that needs a real
datastore with upsert/update semantics. SQLite is used here (not
Postgres) because it ships with Python, needs zero setup, and is more
than enough for an MVP; every function below only uses plain SQL, so
migrating to Postgres later means swapping the connection layer, not
rewriting the queries.

Privacy note
-------------
This database stores OPPORTUNITIES and ALERTS only - never uploaded
resumes or parsed student profiles. A student's parsed profile lives only
in the current Streamlit session (`st.session_state`) and disappears when
the session ends. This follows the project's own security requirement:
"Uploaded resumes should not be unnecessarily persisted or exposed."

Tables
-------
- opportunities   : one row per opportunity, keyed by a deterministic id
                    (see opportunity_sources/base.py: make_opportunity_id)
                    so the same posting from the same source always
                    upserts instead of duplicating.
- alerts          : global, non-personal alerts (new opportunity added,
                    deadline approaching). Personalized "this matches
                    you" alerts are computed live in the app instead of
                    stored, since no student data is persisted.
- update_log      : one row per opportunity_manager sync run, per
                    source - a simple audit trail of when each source was
                    last checked and what happened.
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, List, Optional

from src.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS opportunities (
    id TEXT PRIMARY KEY,
    company TEXT NOT NULL,
    role TEXT NOT NULL,
    description TEXT,
    required_skills TEXT NOT NULL DEFAULT '[]',
    preferred_skills TEXT NOT NULL DEFAULT '[]',
    degree_allowed TEXT,
    branch_allowed TEXT,
    graduation_year_min INTEGER,
    graduation_year_max INTEGER,
    semester_min INTEGER,
    semester_max INTEGER,
    cgpa_min REAL,
    experience_required TEXT,
    location TEXT,
    work_mode TEXT,
    stipend TEXT,
    deadline TEXT,
    role_type TEXT,
    source TEXT NOT NULL,
    source_url TEXT,
    application_url TEXT,
    last_checked TEXT,
    added_at TEXT,
    status TEXT NOT NULL DEFAULT 'UNKNOWN',
    is_demo INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type TEXT NOT NULL,
    opportunity_id TEXT,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (opportunity_id) REFERENCES opportunities (id)
);

CREATE TABLE IF NOT EXISTS update_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_at TEXT NOT NULL,
    source TEXT NOT NULL,
    status TEXT NOT NULL,
    added_count INTEGER DEFAULT 0,
    updated_count INTEGER DEFAULT 0,
    expired_count INTEGER DEFAULT 0,
    message TEXT
);
"""


@contextmanager
def get_connection():
    """Yield a SQLite connection with row access by column name."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Create all tables if they do not already exist. Safe to call every startup."""
    with get_connection() as conn:
        conn.executescript(SCHEMA)


def _row_to_opportunity_dict(row: sqlite3.Row) -> Dict:
    d = dict(row)
    d["required_skills"] = json.loads(d["required_skills"] or "[]")
    d["preferred_skills"] = json.loads(d["preferred_skills"] or "[]")
    d["degree_allowed"] = json.loads(d["degree_allowed"]) if d["degree_allowed"] else None
    d["branch_allowed"] = json.loads(d["branch_allowed"]) if d["branch_allowed"] else None
    d["is_demo"] = bool(d["is_demo"])
    return d


def upsert_opportunity(opportunity: Dict) -> str:
    """
    Insert a new opportunity or update an existing one (matched by id).
    Returns "added" or "updated" so the caller can keep counts.
    """
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM opportunities WHERE id = ?", (opportunity["id"],)
        ).fetchone()

        payload = {
            **opportunity,
            "required_skills": json.dumps(opportunity.get("required_skills", [])),
            "preferred_skills": json.dumps(opportunity.get("preferred_skills", [])),
            "degree_allowed": json.dumps(opportunity["degree_allowed"]) if opportunity.get("degree_allowed") else None,
            "branch_allowed": json.dumps(opportunity["branch_allowed"]) if opportunity.get("branch_allowed") else None,
            "is_demo": int(opportunity.get("is_demo", False)),
        }

        columns = [
            "id", "company", "role", "description", "required_skills", "preferred_skills",
            "degree_allowed", "branch_allowed", "graduation_year_min", "graduation_year_max",
            "semester_min", "semester_max", "cgpa_min", "experience_required", "location",
            "work_mode", "stipend", "deadline", "role_type", "source", "source_url",
            "application_url", "last_checked", "added_at", "status", "is_demo",
        ]

        for col in columns:
            payload.setdefault(col, None)

        if existing:
            set_clause = ", ".join(f"{col} = :{col}" for col in columns if col != "id")
            conn.execute(f"UPDATE opportunities SET {set_clause} WHERE id = :id", payload)
            return "updated"
        else:
            placeholders = ", ".join(f":{col}" for col in columns)
            conn.execute(
                f"INSERT INTO opportunities ({', '.join(columns)}) VALUES ({placeholders})",
                payload,
            )
            return "added"


def get_all_opportunities(include_expired: bool = True) -> List[Dict]:
    """Return every opportunity row as a plain dict, most recently added first."""
    with get_connection() as conn:
        query = "SELECT * FROM opportunities"
        if not include_expired:
            query += " WHERE status NOT IN ('EXPIRED', 'CLOSED')"
        query += " ORDER BY added_at DESC"
        rows = conn.execute(query).fetchall()
        return [_row_to_opportunity_dict(row) for row in rows]


def get_opportunity(opportunity_id: str) -> Optional[Dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM opportunities WHERE id = ?", (opportunity_id,)
        ).fetchone()
        return _row_to_opportunity_dict(row) if row else None


def update_opportunity_status(opportunity_id: str, status: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE opportunities SET status = ? WHERE id = ?", (status, opportunity_id)
        )


def add_alert(alert_type: str, message: str, opportunity_id: Optional[str] = None) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO alerts (alert_type, opportunity_id, message, created_at) VALUES (?, ?, ?, ?)",
            (alert_type, opportunity_id, message, datetime.utcnow().isoformat()),
        )


def get_alerts(limit: int = 50) -> List[Dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM alerts ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(row) for row in rows]


def clear_alerts() -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM alerts")


def log_update_run(source: str, status: str, added: int = 0, updated: int = 0, expired: int = 0, message: str = "") -> None:
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO update_log (run_at, source, status, added_count, updated_count, expired_count, message)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (datetime.utcnow().isoformat(), source, status, added, updated, expired, message),
        )


def get_update_log(limit: int = 20) -> List[Dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM update_log ORDER BY run_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(row) for row in rows]


def reset_db() -> None:
    """Drop and recreate all tables. Useful for tests and for a clean demo reset."""
    with get_connection() as conn:
        conn.executescript(
            "DROP TABLE IF EXISTS opportunities; DROP TABLE IF EXISTS alerts; DROP TABLE IF EXISTS update_log;"
        )
    init_db()


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
