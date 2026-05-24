"""
LinkedIn scraper — uses Google RSS search + public job search URLs.
Direct LinkedIn scraping is blocked; we use RSS feeds and public search pages.
"""

import logging
import feedparser
import requests
from bs4 import BeautifulSoup
from utils.filters import BaseScraper, is_ece_job, extract_skills, HEADERS

logger = logging.getLogger(__name__)

# Google RSS feeds that index LinkedIn job postings
GOOGLE_RSS_LINKEDIN = [
    "https://news.google.com/rss/search?q=embedded+engineer+jobs+india+site:linkedin.com&hl=en-IN&gl=IN",
    "https://news.google.com/rss/search?q=firmware+engineer+jobs+india+site:linkedin.com&hl=en-IN&gl=IN",
    "https://news.google.com/rss/search?q=vlsi+engineer+jobs+india+site:linkedin.com&hl=en-IN&gl=IN",
    "https://news.google.com/rss/search?q=fpga+engineer+india+site:linkedin.com&hl=en-IN&gl=IN",
    "https://news.google.com/rss/search?q=electronics+engineer+india+site:linkedin.com&hl=en-IN&gl=IN",
]

# LinkedIn public job search (no login required for listing page)
LINKEDIN_SEARCH_URLS = [
    "https://www.linkedin.com/jobs/search/?keywords=embedded+engineer&location=India&f_TPR=r86400&sortBy=DD",
    "https://www.linkedin.com/jobs/search/?keywords=firmware+engineer&location=India&f_TPR=r86400&sortBy=DD",
    "https://www.linkedin.com/jobs/search/?keywords=vlsi+engineer&location=India&f_TPR=r86400&sortBy=DD",
    "https://www.linkedin.com/jobs/search/?keywords=fpga+engineer&location=India&f_TPR=r86400&sortBy=DD",
    "https://www.linkedin.com/jobs/search/?keywords=electronics+engineer&location=India&f_TPR=r86400&sortBy=DD",
    "https://www.linkedin.com/jobs/search/?keywords=hardware+engineer&location=India&f_TPR=r86400&sortBy=DD",
]

_HEADERS = {**HEADERS, "Referer": "https://www.linkedin.com/"}


class LinkedInScraper(BaseScraper):
    source = "LinkedIn"

    def scrape(self) -> list[dict]:
        jobs = []
        seen = set()
        fetch_count = 0
        skip_count = 0

        # Method 1: RSS via Google News (most reliable)
        for feed_url in GOOGLE_RSS_LINKEDIN:
            try:
                feed = feedparser.parse(feed_url)
                fetch_count += len(feed.entries)
                for entry in feed.entries:
                    title = entry.get("title", "")
                    link = entry.get("link", "")
                    summary = entry.get("summary", "")

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
                logger.error(f"LinkedIn Google RSS error [{feed_url}]: {e}")

        # Method 2: LinkedIn public search pages
        for url in LINKEDIN_SEARCH_URLS:
            try:
                resp = requests.get(url, headers=_HEADERS, timeout=20)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                cards = soup.select(".base-card, .job-search-card, .jobs-search__results-list li")
                fetch_count += len(cards)

                for card in cards:
                    try:
                        title_el = card.select_one(".base-search-card__title, h3.base-search-card__title")
                        company_el = card.select_one(".base-search-card__subtitle, h4.base-search-card__subtitle")
                        location_el = card.select_one(".job-search-card__location, .base-search-card__metadata span")
                        link_el = card.select_one("a.base-card__full-link, a[href*='/jobs/view/']")

                        if not title_el or not link_el:
                            skip_count += 1
                            continue

                        title = title_el.get_text(strip=True)
                        company = company_el.get_text(strip=True) if company_el else "Unknown"
                        location = location_el.get_text(strip=True) if location_el else "India"
                        link = link_el.get("href", "").split("?")[0]

                        if not link or link in seen:
                            skip_count += 1
                            continue
                        seen.add(link)

                        if not is_ece_job(title, ""):
                            skip_count += 1
                            continue

                        skills = extract_skills(title)
                        jobs.append(self.make_job(
                            title=title,
                            company=company,
                            location=location,
                            link=link,
                            skills=skills,
                        ))
                    except Exception as e:
                        logger.debug(f"LinkedIn card parse error: {e}")
                        skip_count += 1

            except requests.RequestException as e:
                logger.error(f"LinkedIn search request failed [{url}]: {e}")
            except Exception as e:
                logger.error(f"LinkedIn scrape error [{url}]: {e}", exc_info=True)

        logger.info(f"LinkedIn: fetched {fetch_count} entries → {len(jobs)} ECE jobs (skipped {skip_count})")
        return jobs
