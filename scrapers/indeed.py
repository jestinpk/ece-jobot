"""
Indeed scraper — uses RSS feeds for ECE job searches.
No API key required for RSS.
"""

import logging
import feedparser
from utils.filters import BaseScraper, is_ece_job, extract_skills

logger = logging.getLogger(__name__)

# Indeed RSS feed URLs for ECE-related searches
INDEED_RSS_FEEDS = [
    "https://www.indeed.com/rss?q=embedded+engineer&l=&sort=date",
    "https://www.indeed.com/rss?q=VLSI+engineer&l=&sort=date",
    "https://www.indeed.com/rss?q=firmware+engineer&l=&sort=date",
    "https://www.indeed.com/rss?q=FPGA+engineer&l=&sort=date",
    "https://www.indeed.com/rss?q=PCB+hardware+engineer&l=&sort=date",
    "https://www.indeed.com/rss?q=IoT+electronics+engineer&l=&sort=date",
    "https://www.indeed.com/rss?q=telecom+RF+engineer&l=&sort=date",
    "https://www.indeed.com/rss?q=robotics+engineer&l=&sort=date",
]


class IndeedScraper(BaseScraper):
    source = "Indeed"

    def scrape(self) -> list[dict]:
        jobs = []
        seen_links = set()

        for feed_url in INDEED_RSS_FEEDS:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries:
                    title = entry.get("title", "")
                    summary = entry.get("summary", "")
                    link = entry.get("link", "")

                    if link in seen_links:
                        continue
                    seen_links.add(link)

                    if not is_ece_job(title, summary):
                        continue

                    # Parse company and location from title (format: "Title - Company - Location")
                    parts = title.split(" - ")
                    job_title = parts[0].strip() if parts else title
                    company = parts[1].strip() if len(parts) > 1 else "Unknown"
                    location = parts[2].strip() if len(parts) > 2 else "Not specified"

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
                logger.error(f"Indeed RSS feed error ({feed_url}): {e}", exc_info=True)

        return jobs
