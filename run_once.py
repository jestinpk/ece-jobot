"""
Single-cycle runner for GitHub Actions.
- Posts new India ECE jobs (max 5/source, 15 total per run)
- If no new jobs found AND digest not sent today → sends daily digest
- Self-exits at 7 minutes to stay within GitHub's 9-minute timeout
"""

import os
import time
import logging

os.makedirs("data", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ECEJobBot")

from utils.database import Database
from utils.telegram import TelegramBot
from utils.filters import is_indian_job
from scrapers.linkedin import LinkedInScraper
from scrapers.naukri import NaukriScraper
from scrapers.indeed import IndeedScraper
from scrapers.instahyre import InstaHyreScraper
from scrapers.cutshort import CutshortScraper
from scrapers.internshala import IntershalaScraper
from scrapers.freshersworld import FreshersworldScraper
from scrapers.wellfound import WellfoundScraper
from scrapers.googlerss import GoogleRSSScraper
from scrapers.remoteok import RemoteOKScraper

# ── Limits ────────────────────────────────────────────────────────────────────
MAX_JOBS_PER_SOURCE = int(os.environ.get("MAX_JOBS_PER_SOURCE", "5"))
MAX_TOTAL_POSTS     = int(os.environ.get("MAX_TOTAL_POSTS", "15"))
CYCLE_TIMEOUT_SECS  = int(os.environ.get("CYCLE_TIMEOUT_SECS", "420"))
REMOTEOK_THRESHOLD  = 5
# ─────────────────────────────────────────────────────────────────────────────

PRIMARY_SCRAPERS = [
    LinkedInScraper,
    NaukriScraper,
    IndeedScraper,
    InstaHyreScraper,
    CutshortScraper,
    IntershalaScraper,
    FreshersworldScraper,
    WellfoundScraper,
    GoogleRSSScraper,
]


def run():
    cycle_start = time.time()
    logger.info("=== ECE Job Alert Bot — India Priority 🇮🇳 ===")
    logger.info(f"Limits: {MAX_JOBS_PER_SOURCE}/source · {MAX_TOTAL_POSTS} total · {CYCLE_TIMEOUT_SECS}s timeout")

    db  = Database()
    bot = TelegramBot()

    total_fetched    = 0
    total_india      = 0
    total_duplicates = 0
    total_posted     = 0

    def time_left():
        return CYCLE_TIMEOUT_SECS - (time.time() - cycle_start)

    def post_jobs(jobs, source_label):
        nonlocal total_fetched, total_india, total_duplicates, total_posted

        total_fetched += len(jobs)
        india_jobs = [j for j in jobs if is_indian_job(j)]
        dropped = len(jobs) - len(india_jobs)
        total_india += len(india_jobs)

        if dropped:
            logger.info(f"{source_label}: dropped {dropped} non-India jobs")

        posted_this_source = 0
        for job in india_jobs:
            if time_left() < 30:
                logger.warning("⏱ Time budget low — stopping early")
                return
            if total_posted >= MAX_TOTAL_POSTS:
                logger.info(f"🔒 MAX_TOTAL_POSTS ({MAX_TOTAL_POSTS}) reached")
                return
            if posted_this_source >= MAX_JOBS_PER_SOURCE:
                logger.info(f"🔒 {source_label}: per-source limit ({MAX_JOBS_PER_SOURCE}) reached")
                break

            if db.is_duplicate(job["link"]):
                total_duplicates += 1
                logger.debug(f"Duplicate skipped: {job['title']}")
                continue

            if bot.post_job(job):
                db.save_job(job)
                total_posted += 1
                posted_this_source += 1
                logger.info(f"✅ [{total_posted}/{MAX_TOTAL_POSTS}] {job['title']} @ {job['company']} [{source_label}]")
                time.sleep(2)

    # ── Primary scrapers ──────────────────────────────────────────────────────
    for ScraperClass in PRIMARY_SCRAPERS:
        if time_left() < 45 or total_posted >= MAX_TOTAL_POSTS:
            break
        name = ScraperClass.__name__.replace("Scraper", "")
        try:
            post_jobs(ScraperClass().scrape(), name)
        except Exception as e:
            logger.error(f"Error in {name}: {e}", exc_info=True)

    # ── RemoteOK fallback ─────────────────────────────────────────────────────
    if total_india < REMOTEOK_THRESHOLD and time_left() > 45 and total_posted < MAX_TOTAL_POSTS:
        logger.info(f"India jobs low ({total_india}) — trying RemoteOK fallback")
        try:
            post_jobs(RemoteOKScraper().scrape(), "RemoteOK")
        except Exception as e:
            logger.error(f"RemoteOK error: {e}", exc_info=True)
    else:
        logger.info("RemoteOK skipped ✓")

    # ── Daily digest (fires only if nothing was posted today) ─────────────────
    if total_posted == 0:
        if db.digest_already_sent_today():
            logger.info("No new jobs & digest already sent today — nothing to do.")
        else:
            logger.info("No new jobs posted — sending daily digest...")
            recent_jobs  = db.get_recent_jobs(hours=24, limit=10)
            total_in_db  = db.total_jobs_count()
            success      = bot.post_daily_digest(recent_jobs, total_in_db)
            if success:
                db.record_digest_sent()
                logger.info(f"Daily digest sent with {len(recent_jobs)} recent jobs.")
    else:
        logger.info(f"New jobs posted ({total_posted}) — digest skipped.")

    elapsed = round(time.time() - cycle_start, 1)
    logger.info(
        f"━━━ Done in {elapsed}s | Fetched: {total_fetched} | India: {total_india} "
        f"| Dupes: {total_duplicates} | Posted: {total_posted} ━━━"
    )
    db.close()


if __name__ == "__main__":
    run()
