"""
Single-cycle runner for GitHub Actions deployment.
GitHub Actions handles the 10-minute scheduling via cron.
Run bot.py directly for local continuous mode.
"""

import logging
import os
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ECEJobBot")

os.makedirs("data", exist_ok=True)

from utils.database import Database
from utils.telegram import TelegramBot
from scrapers.remoteok import RemoteOKScraper
from scrapers.indeed import IndeedScraper
from scrapers.internshala import IntershalaScraper
from scrapers.freshersworld import FreshersworldScraper


def run():
    logger.info("=== ECE Job Alert Bot — Single Cycle ===")
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
            logger.info(f"{scraper.__class__.__name__}: {len(jobs)} ECE jobs found")
            for job in jobs:
                if not db.is_duplicate(job["link"]):
                    success = bot.post_job(job)
                    if success:
                        db.save_job(job)
                        total_new += 1
                        time.sleep(2)
        except Exception as e:
            logger.error(f"Scraper error in {scraper.__class__.__name__}: {e}", exc_info=True)

    logger.info(f"Done. {total_new} new jobs posted.")
    db.close()


if __name__ == "__main__":
    run()
