"""
ECE Job Alert Bot - Main Entry Point
Scrapes ECE jobs and posts to Telegram every 10 minutes.
"""

import time
import logging
import schedule
from utils.database import Database
from utils.telegram import TelegramBot
from scrapers.remoteok import RemoteOKScraper
from scrapers.indeed import IndeedScraper
from scrapers.internshala import IntershalaScraper
from scrapers.freshersworld import FreshersworldScraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ECEJobBot")


def run_job_cycle():
    """Single cycle: scrape → filter → post new jobs."""
    logger.info("Starting job scraping cycle...")
    db = Database()
    bot = TelegramBot()

    scrapers = [
        RemoteOKScraper(),
        IndeedScraper(),
        IntershalaScraper(),
        FreshersworldScraper(),
    ]

    total_new = 0
    for scraper in scrapers:
        try:
            jobs = scraper.scrape()
            logger.info(f"{scraper.__class__.__name__}: found {len(jobs)} ECE jobs")
            for job in jobs:
                if not db.is_duplicate(job["link"]):
                    success = bot.post_job(job)
                    if success:
                        db.save_job(job)
                        total_new += 1
                        time.sleep(2)  # Avoid Telegram rate limits
        except Exception as e:
            logger.error(f"Error in {scraper.__class__.__name__}: {e}", exc_info=True)

    logger.info(f"Cycle complete. Posted {total_new} new jobs.")
    db.close()


def main():
    logger.info("ECE Job Alert Bot started.")
    run_job_cycle()  # Run immediately on start
    schedule.every(10).minutes.do(run_job_cycle)
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
