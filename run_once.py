"""
Single-cycle runner for GitHub Actions.
GitHub Actions handles the 10-minute cron scheduling.
Run bot.py for local continuous mode.
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

REMOTEOK_THRESHOLD = 5


def run():
    logger.info("=== ECE Job Alert Bot v2 — India Priority Mode 🇮🇳 ===")

    db = Database()
    bot = TelegramBot()

    primary_scrapers = [
        LinkedInScraper(),
        NaukriScraper(),
        IndeedScraper(),
        InstaHyreScraper(),
        CutshortScraper(),
        IntershalaScraper(),
        FreshersworldScraper(),
        WellfoundScraper(),
        GoogleRSSScraper(),
    ]

    total_fetched = 0
    total_india = 0
    total_duplicates = 0
    total_posted = 0

    for scraper in primary_scrapers:
        name = scraper.__class__.__name__
        try:
            jobs = scraper.scrape()
            total_fetched += len(jobs)

            india_jobs = [j for j in jobs if is_indian_job(j)]
            non_india = len(jobs) - len(india_jobs)
            total_india += len(india_jobs)

            if non_india:
                logger.info(f"{name}: filtered out {non_india} non-India jobs")

            for job in india_jobs:
                if db.is_duplicate(job["link"]):
                    total_duplicates += 1
                    logger.debug(f"Duplicate skipped: {job['title']}")
                    continue

                success = bot.post_job(job)
                if success:
                    db.save_job(job)
                    total_posted += 1
                    logger.info(f"✅ Posted: {job['title']} @ {job['company']} [{job['source']}]")
                    time.sleep(2)

        except Exception as e:
            logger.error(f"Error in {name}: {e}", exc_info=True)

    # RemoteOK fallback
    if total_india < REMOTEOK_THRESHOLD:
        logger.info(f"Activating RemoteOK fallback (india={total_india} < threshold={REMOTEOK_THRESHOLD})")
        try:
            fallback = RemoteOKScraper().scrape()
            total_fetched += len(fallback)
            for job in fallback:
                if db.is_duplicate(job["link"]):
                    total_duplicates += 1
                    continue
                if bot.post_job(job):
                    db.save_job(job)
                    total_posted += 1
                    time.sleep(2)
        except Exception as e:
            logger.error(f"RemoteOK fallback error: {e}", exc_info=True)

    logger.info(
        f"Done | Fetched: {total_fetched} | India: {total_india} "
        f"| Duplicates: {total_duplicates} | Posted: {total_posted}"
    )
    db.close()


if __name__ == "__main__":
    run()
