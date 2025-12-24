import sqlite3
import threading
import time


class Database:
    def __init__(self, path: str) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")

    def init(self) -> None:
        with self._lock:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    legal_accepted INTEGER NOT NULL DEFAULT 0,
                    legal_accepted_at INTEGER,
                    created_at INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS outages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    reward TEXT,
                    starts_at INTEGER NOT NULL,
                    ends_at INTEGER NOT NULL,
                    created_at INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    outage_id INTEGER NOT NULL,
                    send_at INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    sent_at INTEGER,
                    FOREIGN KEY (outage_id) REFERENCES outages (id) ON DELETE CASCADE,
                    UNIQUE (outage_id, type)
                );

                CREATE INDEX IF NOT EXISTS idx_reminders_send_at
                ON reminders (send_at);
                """
            )
            self._conn.commit()

    def ensure_user(self, user_id: int) -> None:
        now_ts = int(time.time())
        with self._lock:
            self._conn.execute(
                "INSERT OR IGNORE INTO users (user_id, created_at) VALUES (?, ?)",
                (user_id, now_ts),
            )
            self._conn.commit()

    def set_legal_accepted(self, user_id: int, accepted_at: int | None = None) -> None:
        if accepted_at is None:
            accepted_at = int(time.time())
        with self._lock:
            self._conn.execute(
                "INSERT OR IGNORE INTO users (user_id, created_at) VALUES (?, ?)",
                (user_id, accepted_at),
            )
            self._conn.execute(
                "UPDATE users SET legal_accepted = 1, legal_accepted_at = ? WHERE user_id = ?",
                (accepted_at, user_id),
            )
            self._conn.commit()

    def is_legal_accepted(self, user_id: int) -> bool:
        with self._lock:
            row = self._conn.execute(
                "SELECT legal_accepted FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        return bool(row["legal_accepted"]) if row else False

    def list_user_ids(self, only_accepted: bool = True) -> list[int]:
        query = "SELECT user_id FROM users"
        params: tuple = ()
        if only_accepted:
            query += " WHERE legal_accepted = 1"
        with self._lock:
            rows = self._conn.execute(query, params).fetchall()
        return [int(row["user_id"]) for row in rows]

    def create_outage(self, name: str, reward: str | None, starts_at: int, ends_at: int) -> int:
        now_ts = int(time.time())
        with self._lock:
            cursor = self._conn.execute(
                """
                INSERT INTO outages (name, reward, starts_at, ends_at, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, reward, starts_at, ends_at, now_ts),
            )
            self._conn.commit()
            return int(cursor.lastrowid)

    def delete_outage_by_name(self, name: str) -> int:
        with self._lock:
            cursor = self._conn.execute(
                "DELETE FROM outages WHERE name = ?",
                (name,),
            )
            self._conn.commit()
        return int(cursor.rowcount)

    def create_reminders(self, outage_id: int, reminders: list[tuple[str, int]]) -> int:
        now_ts = int(time.time())
        rows = [(outage_id, send_at, reminder_type, now_ts) for reminder_type, send_at in reminders]
        with self._lock:
            self._conn.executemany(
                """
                INSERT OR IGNORE INTO reminders (outage_id, send_at, type, created_at)
                VALUES (?, ?, ?, ?)
                """,
                rows,
            )
            self._conn.commit()
        return len(rows)

    def get_due_reminders(self, now_ts: int) -> list[sqlite3.Row]:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT r.id, r.type, r.send_at, o.name, o.reward, o.starts_at, o.ends_at
                FROM reminders r
                JOIN outages o ON o.id = r.outage_id
                WHERE r.sent_at IS NULL AND r.send_at <= ?
                ORDER BY r.send_at ASC
                """,
                (now_ts,),
            ).fetchall()
        return rows

    def mark_reminder_sent(self, reminder_id: int, sent_at: int | None = None) -> None:
        if sent_at is None:
            sent_at = int(time.time())
        with self._lock:
            self._conn.execute(
                "UPDATE reminders SET sent_at = ? WHERE id = ?",
                (sent_at, reminder_id),
            )
            self._conn.commit()
