"""
SQLite database for duplicate prevention and job storage.
"""

import sqlite3
import logging
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = "data/jobs.db"


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self._create_tables()

    def _create_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                link_hash TEXT UNIQUE NOT NULL,
                link TEXT NOT NULL,
                title TEXT,
                company TEXT,
                location TEXT,
                source TEXT,
                posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def is_duplicate(self, link: str) -> bool:
        h = hashlib.md5(link.encode()).hexdigest()
        cur = self.conn.execute("SELECT 1 FROM jobs WHERE link_hash = ?", (h,))
        return cur.fetchone() is not None

    def save_job(self, job: dict):
        h = hashlib.md5(job["link"].encode()).hexdigest()
        try:
            self.conn.execute(
                "INSERT INTO jobs (link_hash, link, title, company, location, source) VALUES (?,?,?,?,?,?)",
                (h, job["link"], job.get("title"), job.get("company"),
                 job.get("location"), job.get("source"))
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass  # Race condition — already exists

    def close(self):
        self.conn.close()
