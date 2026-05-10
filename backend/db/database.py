from __future__ import annotations

import sqlite3

from ..config import settings

# Demo organisations — seeded once on first startup.
# API keys use "sk_" prefix so the auth layer can detect them without a DB hit.
_DEMO_ORGS = [
    ("org_acme",    "Acme Pharma",    "pro",        "sk_acme_demo_key"),
    ("org_globex",  "Globex Biotech", "enterprise", "sk_globex_demo_key"),
    ("org_initech", "Initech LLC",    "free",       "sk_initech_demo_key"),
]


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables and seed demo orgs. Safe to call multiple times."""
    conn = get_db()
    with conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS orgs (
                id          TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                plan        TEXT NOT NULL DEFAULT 'free',
                api_key     TEXT UNIQUE,
                created_at  TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS usage_logs (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id        TEXT    NOT NULL REFERENCES orgs(id),
                user_id       TEXT    NOT NULL,
                agent         TEXT    NOT NULL,
                model         TEXT    NOT NULL,
                input_tokens  INTEGER NOT NULL DEFAULT 0,
                output_tokens INTEGER NOT NULL DEFAULT 0,
                cost_usd      REAL    NOT NULL DEFAULT 0.0,
                company_name  TEXT,
                created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS chat_sessions (
                id         TEXT PRIMARY KEY,
                org_id     TEXT NOT NULL REFERENCES orgs(id),
                user_id    TEXT NOT NULL,
                title      TEXT NOT NULL DEFAULT 'New conversation',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS chat_messages (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  TEXT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
                role        TEXT NOT NULL,   -- 'user' | 'assistant'
                content     TEXT NOT NULL,   -- plain text for user; assistant commentary text
                result_type TEXT,            -- NULL | 'research' | 'brief'
                result_data TEXT,            -- JSON blob of the full result object
                created_at  TEXT NOT NULL DEFAULT (datetime('now'))
            );
        """)
        conn.executemany(
            "INSERT OR IGNORE INTO orgs (id, name, plan, api_key) VALUES (?, ?, ?, ?)",
            _DEMO_ORGS,
        )
    conn.close()
