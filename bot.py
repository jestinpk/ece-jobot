"""
ECE Job Alert Bot — Main Entry Point (local continuous mode).
Posts India ECE jobs to Telegram every 10 minutes.
Priority: LinkedIn > Naukri > Indeed India > Instahyre > Cutshort
         > Internshala > Freshersworld > Wellfound > GoogleRSS
         > RemoteOK (fallback only if Indian sources yield < 5 jobs)
"""

import os
import time
import logging
import schedule

os.makedirs("data", exist_ok=True)

from utils.database import Database
from utils.telegram import TelegramBot
from utils.filters import is_indian_job

# Primary India sources (priority order)
from scrapers.linkedin import LinkedInScraper
from scrapers.naukri import NaukriScraper
from scrapers.indeed import IndeedScraper
from scrapers.instahyre import InstaHyreScraper
from scrapers.cutshort import CutshortScraper
from scrapers.internshala import IntershalaScraper
from scrapers.freshersworld import FreshersworldScraper
from scrapers.wellfound import WellfoundScraper
from scrapers.googlerss import GoogleRSSScraper

# Fallback only
from scrapers.remoteok import RemoteOKScraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ECEJobBot")

REMOTEOK_THRESHOLD = 5  # Use RemoteOK only if India sources return fewer than this


def run_job_cycle():
    """Single cycle: scrape → India-filter → deduplicate → post."""
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("Starting ECE job scraping cycle (India focus)...")

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
                    logger.debug(f"Duplicate skipped: {job['title']} [{job['source']}]")
                    continue

                success = bot.post_job(job)
                if success:
                    db.save_job(job)
                    total_posted += 1
                    logger.info(f"✅ Posted: {job['title']} @ {job['company']} [{job['source']}]")
                    time.sleep(2)  # Telegram rate limit

        except Exception as e:
            logger.error(f"Error in {name}: {e}", exc_info=True)

    # RemoteOK fallback
    if total_india < REMOTEOK_THRESHOLD:
        logger.info(f"India jobs below threshold ({total_india} < {REMOTEOK_THRESHOLD}). Activating RemoteOK fallback...")
        try:
            fallback_jobs = RemoteOKScraper().scrape()
            total_fetched += len(fallback_jobs)
            for job in fallback_jobs:
                if db.is_duplicate(job["link"]):
                    total_duplicates += 1
                    continue
                success = bot.post_job(job)
                if success:
                    db.save_job(job)
                    total_posted += 1
                    time.sleep(2)
        except Exception as e:
            logger.error(f"RemoteOK fallback error: {e}", exc_info=True)
    else:
        logger.info("RemoteOK skipped — sufficient India jobs found.")

    logger.info(
        f"Cycle complete | Fetched: {total_fetched} | India: {total_india} "
        f"| Duplicates: {total_duplicates} | Posted: {total_posted}"
    )
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    db.close()


def main():
    logger.info("ECE Job Alert Bot v2 started — India Priority Mode 🇮🇳")
    run_job_cycle()
    schedule.every(10).minutes.do(run_job_cycle)
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
