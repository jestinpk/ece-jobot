"""
SQLite database for duplicate prevention, job storage, and digest queries.
"""

import sqlite3
import logging
import hashlib
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

DB_PATH = "data/jobs.db"


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
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
        # Tracks when daily digest was last sent
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS digest_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            pass

    def get_recent_jobs(self, hours: int = 24, limit: int = 10) -> list:
        """Return jobs posted in the last N hours, newest first."""
        since = datetime.utcnow() - timedelta(hours=hours)
        cur = self.conn.execute(
            """SELECT title, company, location, link, source
               FROM jobs
               WHERE posted_at >= ?
               ORDER BY posted_at DESC
               LIMIT ?""",
            (since.isoformat(), limit)
        )
        return [dict(row) for row in cur.fetchall()]

    def digest_already_sent_today(self) -> bool:
        """Return True if a digest was already sent in the last 23 hours."""
        since = datetime.utcnow() - timedelta(hours=23)
        cur = self.conn.execute(
            "SELECT 1 FROM digest_log WHERE sent_at >= ?",
            (since.isoformat(),)
        )
        return cur.fetchone() is not None

    def record_digest_sent(self):
        self.conn.execute("INSERT INTO digest_log (sent_at) VALUES (?)",
                          (datetime.utcnow().isoformat(),))
        self.conn.commit()

    def total_jobs_count(self) -> int:
        cur = self.conn.execute("SELECT COUNT(*) FROM jobs")
        return cur.fetchone()[0]

    def close(self):
        self.conn.close()
