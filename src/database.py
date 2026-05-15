"""
Database layer for the Trust & Safety Workflow Intelligence Dashboard.

The app uses a local SQLite file as its single source of truth. On first run
the database is seeded from ``data/sample_tickets.csv``. Everything is fully
synthetic -- there is no real user data anywhere in this project.

Keeping all data access in this one module means the rest of the app never
touches SQL directly, which keeps things easy to read and easy to swap out for
a real database later.
"""

from __future__ import annotations

import os
import sqlite3

import pandas as pd

# Resolve paths relative to the project root so the app works no matter where
# Streamlit is launched from.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "tickets.db")
CSV_PATH = os.path.join(PROJECT_ROOT, "data", "sample_tickets.csv")

# Column order used by the tickets table.
TICKET_COLUMNS = [
    "ticket_id",
    "content_type",
    "category",
    "priority",
    "status",
    "assigned_team",
    "created_date",
    "resolved_date",
    "resolution_time_hours",
    "region",
    "short_description",
]


def _connect() -> sqlite3.Connection:
    """Open a SQLite connection. ``check_same_thread`` is False because
    Streamlit may call this from different threads."""
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db(force_reload: bool = False) -> None:
    """Create the tickets table and seed it from the CSV if needed.

    Parameters
    ----------
    force_reload:
        When True, drop and rebuild the table from the CSV. Useful if the
        sample data is regenerated.
    """
    conn = _connect()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id            TEXT PRIMARY KEY,
            content_type         TEXT,
            category             TEXT,
            priority             TEXT,
            status               TEXT,
            assigned_team        TEXT,
            created_date         TEXT,
            resolved_date        TEXT,
            resolution_time_hours REAL,
            region               TEXT,
            short_description    TEXT
        )
        """
    )

    cur.execute("SELECT COUNT(*) FROM tickets")
    row_count = cur.fetchone()[0]

    if force_reload:
        cur.execute("DELETE FROM tickets")
        conn.commit()
        row_count = 0

    if row_count == 0:
        df = pd.read_csv(CSV_PATH)
        # Normalise empty strings to None so SQLite stores proper NULLs.
        df = df.where(pd.notnull(df), None)
        df.to_sql("tickets", conn, if_exists="append", index=False)
        conn.commit()

    conn.close()


def load_tickets() -> pd.DataFrame:
    """Return all tickets as a tidy DataFrame with parsed dates.

    A computed ``age_days`` column is added (how long since the ticket was
    created), which several downstream features rely on.
    """
    init_db()
    conn = _connect()
    df = pd.read_sql_query("SELECT * FROM tickets", conn)
    conn.close()

    df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce")
    df["resolved_date"] = pd.to_datetime(df["resolved_date"], errors="coerce")
    df["resolution_time_hours"] = pd.to_numeric(
        df["resolution_time_hours"], errors="coerce"
    )

    now = pd.Timestamp.now()
    df["age_days"] = ((now - df["created_date"]).dt.total_seconds() / 86400).round(1)

    return df


def get_ticket(ticket_id: str) -> dict | None:
    """Return a single ticket as a dict, or None if it does not exist."""
    df = load_tickets()
    match = df[df["ticket_id"] == ticket_id]
    if match.empty:
        return None
    return match.iloc[0].to_dict()


def reset_database() -> None:
    """Delete the SQLite file entirely so it is rebuilt from the CSV."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
