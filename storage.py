"""Persistent local deduplication. Message bodies are never stored."""
from pathlib import Path
import hashlib
import sqlite3


class State:
    def __init__(self, db_path=".state/messages.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(db_path)
        self.db.execute("CREATE TABLE IF NOT EXISTS handled (key TEXT PRIMARY KEY, status TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        self.db.commit()

    @staticmethod
    def fingerprint(thread, message_id, text):
        return hashlib.sha256(f"{thread}\x00{message_id}\x00{text}".encode("utf-8")).hexdigest()

    def status(self, key):
        row = self.db.execute("SELECT status FROM handled WHERE key=?", (key,)).fetchone()
        return row[0] if row else None

    def mark(self, key, status="done"):
        self.db.execute("INSERT INTO handled (key,status) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET status=excluded.status", (key,status))
        self.db.commit()

    def claim_thread(self, thread_id):
        """Durable at-most-one send attempt per thread for controlled testing.

        A successful claim remains held even if LinkedIn times out after clicking
        Send. This intentionally favors missing a reply over duplicate messages.
        """
        key = self.fingerprint("thread-send-once", thread_id, "v1")
        cursor = self.db.execute(
            "INSERT OR IGNORE INTO handled (key,status) VALUES (?,?)",
            (key, "send-attempted"))
        self.db.commit()
        return cursor.rowcount == 1
