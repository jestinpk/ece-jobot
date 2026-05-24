"""
Google RSS backup source — searches Google News RSS for ECE jobs in India.
Catches listings from Naukri, LinkedIn, Times Jobs, Shine, etc.
"""

import logging
import feedparser
from utils.filters import BaseScraper, is_ece_job, extract_skills, HEADERS

logger = logging.getLogger(__name__)

GOOGLE_RSS_FEEDS = [
    "https://news.google.com/rss/search?q=embedded+engineer+jobs+india&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=firmware+engineer+india+hiring&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=vlsi+jobs+india+bangalore&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=fpga+engineer+india+jobs&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=electronics+hardware+engineer+jobs+india&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=iot+embedded+linux+jobs+india&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=semiconductor+chip+design+jobs+india&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=PCB+design+engineer+india+jobs&hl=en-IN&gl=IN&ceid=IN:en",
]

# Domains that are typically job listings (not news articles)
JOB_DOMAINS = [
    "naukri.com", "linkedin.com", "indeed.com", "shine.com",
    "timesjobs.com", "monsterindia.com", "foundit.in", "freshersworld.com",
    "internshala.com", "cutshort.io", "instahyre.com", "wellfound.com",
]


class GoogleRSSScraper(BaseScraper):
    source = "GoogleRSS"

    def scrape(self) -> list[dict]:
        jobs = []
        seen = set()
        fetch_count = 0
        skip_count = 0

        for feed_url in GOOGLE_RSS_FEEDS:
            try:
                feed = feedparser.parse(feed_url, request_headers=HEADERS)
                fetch_count += len(feed.entries)

                for entry in feed.entries:
                    title = entry.get("title", "")
                    link = entry.get("link", "")
                    summary = entry.get("summary", "")
                    source_url = entry.get("source", {}).get("href", link)

                    if not link or link in seen:
                        skip_count += 1
                        continue
                    seen.add(link)

                    if not is_ece_job(title, summary):
                        skip_count += 1
                        continue

                    skills = extract_skills(f"{title} {summary}")
                    jobs.append(self.make_job(
                        title=title,
                        company="See listing",
                        location="India",
                        link=link,
                        skills=skills,
                        description=summary,
                    ))

            except Exception as e:
                logger.error(f"Google RSS error [{feed_url}]: {e}")

        logger.info(f"GoogleRSS: fetched {fetch_count} entries → {len(jobs)} ECE jobs (skipped {skip_count})")
        return jobs
