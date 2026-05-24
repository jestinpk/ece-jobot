"""
Indeed India scraper — RSS feeds targeting India locations.
"""

import logging
import feedparser
from utils.filters import BaseScraper, is_ece_job, extract_skills, HEADERS

logger = logging.getLogger(__name__)

# Indeed India RSS feeds — all pinned to l=India
INDEED_RSS_FEEDS = [
    "https://in.indeed.com/rss?q=embedded+engineer&l=India&sort=date",
    "https://in.indeed.com/rss?q=VLSI+engineer&l=India&sort=date",
    "https://in.indeed.com/rss?q=firmware+engineer&l=India&sort=date",
    "https://in.indeed.com/rss?q=FPGA+engineer&l=India&sort=date",
    "https://in.indeed.com/rss?q=electronics+engineer&l=India&sort=date",
    "https://in.indeed.com/rss?q=hardware+engineer&l=India&sort=date",
    "https://in.indeed.com/rss?q=IoT+engineer&l=India&sort=date",
    "https://in.indeed.com/rss?q=PCB+design+engineer&l=India&sort=date",
    "https://in.indeed.com/rss?q=semiconductor+engineer&l=India&sort=date",
    "https://in.indeed.com/rss?q=robotics+engineer&l=India&sort=date",
]


class IndeedScraper(BaseScraper):
    source = "Indeed India"

    def scrape(self) -> list[dict]:
        jobs = []
        seen_links = set()
        fetch_count = 0
        skip_count = 0

        for feed_url in INDEED_RSS_FEEDS:
            try:
                feed = feedparser.parse(feed_url, request_headers=HEADERS)
                fetch_count += len(feed.entries)

                for entry in feed.entries:
                    title = entry.get("title", "")
                    summary = entry.get("summary", "")
                    link = entry.get("link", "")

                    if not link or link in seen_links:
                        skip_count += 1
                        continue
                    seen_links.add(link)

                    if not is_ece_job(title, summary):
                        skip_count += 1
                        continue

                    # Indeed title format: "Job Title - Company - Location"
                    parts = [p.strip() for p in title.split(" - ")]
                    job_title = parts[0] if parts else title
                    company = parts[1] if len(parts) > 1 else "Unknown"
                    location = parts[2] if len(parts) > 2 else "India"

                    skills = extract_skills(f"{title} {summary}")
                    jobs.append(self.make_job(
                        title=job_title,
                        company=company,
                        location=location,
                        link=link,
                        skills=skills,
                        description=summary,
                    ))

            except Exception as e:
                logger.error(f"Indeed India RSS error [{feed_url}]: {e}")

        logger.info(f"Indeed India: fetched {fetch_count} entries → {len(jobs)} ECE jobs (skipped {skip_count})")
        return jobs
