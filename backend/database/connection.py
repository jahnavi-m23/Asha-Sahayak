import os
import sqlite3
from pathlib import Path
from contextlib import contextmanager

# Define database file path relative to backend directory
DB_DIR = Path(__file__).resolve().parent
DB_FILE = DB_DIR / "asha_sahayak.db"

def get_db_connection():
    """
    Creates and returns a SQLite connection with row factory enabled
    and foreign key constraints enforced.
    """
    conn = sqlite3.connect(
        str(DB_FILE),
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    # Enforce foreign keys and enable Write-Ahead Logging for high concurrency
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

@contextmanager
def get_db():
    """
    Context manager for database transactions.
    Automatically commits on success or rolls back on exception.
    """
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
