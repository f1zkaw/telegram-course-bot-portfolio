"""SQLite storage for demo bot. The actual database must NEVER go to GitHub."""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Storage:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)

    def _connect(self):
        return sqlite3.connect(self.db_path, timeout=20)

    def init_db(self):
        with self._connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    has_access INTEGER NOT NULL DEFAULT 0,
                    current_lesson INTEGER NOT NULL DEFAULT 0,
                    last_daily_message_at TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    request_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    amount_minor INTEGER NOT NULL,
                    currency TEXT NOT NULL,
                    provider_charge_id TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL
                );
            """)

    def touch_user(self, user_id: int, username: str | None):
        with self._connect() as db:
            db.execute("""
                INSERT INTO users(user_id, username, created_at)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET username = excluded.username
            """, (user_id, username, now_iso()))

    def get_user(self, user_id: int) -> dict | None:
        with self._connect() as db:
            row = db.execute("""
                SELECT user_id, username, has_access, current_lesson,
                       last_daily_message_at
                  FROM users WHERE user_id = ?
            """, (user_id,)).fetchone()
        if row is None:
            return None
        return {
            "user_id": row[0], "username": row[1],
            "has_access": bool(row[2]), "current_lesson": row[3],
            "last_daily_message_at": row[4],
        }

    def set_access(self, user_id: int, has_access: bool = True):
        with self._connect() as db:
            db.execute("UPDATE users SET has_access = ? WHERE user_id = ?",
                       (int(has_access), user_id))

    def set_lesson(self, user_id: int, number: int):
        with self._connect() as db:
            db.execute("UPDATE users SET current_lesson = ? WHERE user_id = ?",
                       (number, user_id))

    def set_last_daily(self, user_id: int, timestamp: str):
        with self._connect() as db:
            db.execute("UPDATE users SET last_daily_message_at = ? WHERE user_id = ?",
                       (timestamp, user_id))

    def save_request(self, user_id: int, content: str):
        with self._connect() as db:
            db.execute("""
                INSERT INTO requests(user_id, request_type, content, created_at)
                VALUES (?, 'consultation', ?, ?)
            """, (user_id, content, now_iso()))

    def record_payment(self, user_id: int, amount_minor: int,
                       currency: str, charge_id: str) -> bool:
        """Idempotent receipt insert and grant of access in one transaction."""
        with self._connect() as db:
            cursor = db.execute("""
                INSERT OR IGNORE INTO payments
                    (user_id, amount_minor, currency, provider_charge_id, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, amount_minor, currency, charge_id, now_iso()))
            if cursor.rowcount:
                db.execute("UPDATE users SET has_access = 1 WHERE user_id = ?", (user_id,))
                return True
            return False
