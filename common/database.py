"""Connection factory for the SQLite database."""

import sqlite3
from pathlib import Path


def get_connection(db_path: str, readonly: bool = True) -> sqlite3.Connection:
    """Open a SQLite connection.

    Args:
        db_path: Path to the SQLite database file.
        readonly: If True, opens with ?mode=ro URI and enables query_only PRAGMA.

    Returns:
        A sqlite3.Connection with row_factory set to sqlite3.Row,
        busy_timeout of 30s, and WAL journal mode.
    """
    if readonly:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        conn.execute("PRAGMA query_only = ON")
    else:
        conn = sqlite3.connect(db_path)

    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 30000")
    if not readonly:
        conn.execute("PRAGMA journal_mode = WAL")
    return conn
