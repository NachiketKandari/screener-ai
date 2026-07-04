"""Connection factory for SQLite / Turso (libsql) databases.

Auto-selects backend based on environment variables:
- TURSO_URL + TURSO_AUTH_TOKEN set  -> Turso embedded replica mode
- Neither set                         -> native sqlite3 (backward compatible)
"""

import os
import sqlite3 as _sqlite3
from typing import Any

# ---------------------------------------------------------------------------
# Optional libsql import
# ---------------------------------------------------------------------------
try:
    import libsql as _libsql
    _TURSO_AVAILABLE = True
except ImportError:
    _libsql = None
    _TURSO_AVAILABLE = False


# ---------------------------------------------------------------------------
# DatabaseRow — tuple wrapper with dict-like column access
# ---------------------------------------------------------------------------

class DatabaseRow:
    """Drop-in replacement for sqlite3.Row supporting row['col'] and row[0].

    libsql returns plain tuples; this bridges to dict-like access used
    throughout the codebase.  sqlite3.Row instances pass through untouched.
    """

    __slots__ = ("_colmap", "_values")

    def __init__(self, columns: tuple[str, ...], values: tuple) -> None:
        self._colmap = {name: idx for idx, name in enumerate(columns)}
        self._values = values

    def __getitem__(self, key: str | int) -> Any:
        if isinstance(key, str):
            return self._values[self._colmap[key]]
        return self._values[key]

    def __len__(self) -> int:
        return len(self._values)

    def __iter__(self):
        return iter(self._values)

    def __repr__(self) -> str:
        return f"Row({dict(zip(self._colmap.keys(), self._values))})"


# ---------------------------------------------------------------------------
# DatabaseCursor — wraps a raw cursor to return DatabaseRow / sqlite3.Row
# ---------------------------------------------------------------------------

class DatabaseCursor:
    """Cursor wrapper that returns DatabaseRow for libsql, passes sqlite3.Row through."""

    def __init__(self, raw_cursor, description) -> None:
        self._cursor = raw_cursor
        self._columns = tuple(d[0] for d in description) if description else ()
        self._description = description

    @property
    def description(self):
        return self._description

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None:
            return None
        if isinstance(row, _sqlite3.Row):
            return row
        return DatabaseRow(self._columns, row)

    def fetchall(self) -> list:
        rows = self._cursor.fetchall()
        if rows and isinstance(rows[0], _sqlite3.Row):
            return rows
        return [DatabaseRow(self._columns, r) for r in rows]

    def __iter__(self):
        for row in self._cursor:
            if isinstance(row, _sqlite3.Row):
                yield row
            else:
                yield DatabaseRow(self._columns, row)


# ---------------------------------------------------------------------------
# DatabaseConnection — uniform interface over sqlite3 and libsql
# ---------------------------------------------------------------------------

class DatabaseConnection:
    """Wraps an sqlite3 or libsql connection behind a uniform interface."""

    def __init__(self, raw_conn, is_libsql: bool = False) -> None:
        self._conn = raw_conn
        self._is_libsql = is_libsql

    def execute(self, sql: str, params=None) -> DatabaseCursor:
        cursor = self._conn.execute(sql, params) if params is not None else self._conn.execute(sql)
        return DatabaseCursor(cursor, cursor.description)

    def fetchone(self, sql: str, params=None):
        """Convenience: execute + fetchone in one call."""
        return self.execute(sql, params).fetchone()

    def fetchall(self, sql: str, params=None) -> list:
        """Convenience: execute + fetchall in one call."""
        return self.execute(sql, params).fetchall()

    def close(self) -> None:
        self._conn.close()

    def commit(self) -> None:
        self._conn.commit()

    def sync(self) -> None:
        """Sync local embedded replica with Turso primary. No-op for sqlite3."""
        if self._is_libsql:
            self._conn.sync()

    # -- context manager support --------------------------------------------

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type is None:
            try:
                self.commit()
            except Exception:
                pass
        try:
            self.close()
        except Exception:
            pass
        return False


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_connection(db_path: str, readonly: bool = True) -> DatabaseConnection:
    """Open a database connection, auto-selecting sqlite3 or Turso.

    Turso mode activates when both TURSO_URL and TURSO_AUTH_TOKEN env vars
    are set and non-empty.  Otherwise native sqlite3 is used.
    """
    turso_url = os.environ.get("TURSO_URL", "").strip()
    turso_token = os.environ.get("TURSO_AUTH_TOKEN", "").strip()

    if turso_url and turso_token:
        return _connect_turso(db_path, turso_url, turso_token)
    return _connect_sqlite(db_path, readonly)


def _connect_sqlite(db_path: str, readonly: bool) -> DatabaseConnection:
    """Open a native sqlite3 connection (preserves existing behaviour)."""
    if readonly:
        conn = _sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        conn.execute("PRAGMA query_only = ON")
    else:
        conn = _sqlite3.connect(db_path)

    conn.row_factory = _sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 30000")
    if not readonly:
        conn.execute("PRAGMA journal_mode = WAL")
    return DatabaseConnection(conn, is_libsql=False)


def _connect_turso(db_path: str, url: str, token: str) -> DatabaseConnection:
    """Open a libsql embedded replica connection."""
    if not _TURSO_AVAILABLE:
        raise RuntimeError(
            "Turso is configured (TURSO_URL is set) but libsql is not installed. "
            "Run: pip install libsql"
        )
    # If a plain SQLite file exists at db_path, move it aside so libsql
    # can create a fresh embedded replica synced from Turso.
    if os.path.exists(db_path):
        backup = db_path + ".pre-turso"
        os.rename(db_path, backup)
    sync_interval = int(os.environ.get("TURSO_SYNC_INTERVAL", "60"))
    conn = _libsql.connect(
        db_path,
        sync_url=url,
        auth_token=token,
        sync_interval=sync_interval,
    )
    return DatabaseConnection(conn, is_libsql=True)
