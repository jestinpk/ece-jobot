"""
Naukri scraper — India's largest job portal, ECE/electronics roles.
Uses public search pages + RSS fallback via Google News.
"""

import logging
import feedparser
import requests
from bs4 import BeautifulSoup
from utils.filters import BaseScraper, is_ece_job, extract_skills, HEADERS

logger = logging.getLogger(__name__)

_HEADERS = {
    **HEADERS,
    "Referer": "https://www.naukri.com/",
    "X-Requested-With": "XMLHttpRequest",
}

NAUKRI_URLS = [
    "https://www.naukri.com/embedded-engineer-jobs",
    "https://www.naukri.com/vlsi-engineer-jobs",
    "https://www.naukri.com/firmware-engineer-jobs",
    "https://www.naukri.com/hardware-engineer-jobs",
    "https://www.naukri.com/fpga-engineer-jobs",
    "https://www.naukri.com/electronics-engineer-jobs",
    "https://www.naukri.com/iot-engineer-jobs",
    "https://www.naukri.com/pcb-design-engineer-jobs",
    "https://www.naukri.com/semiconductor-jobs",
]

# Google RSS as Naukri fallback
NAUKRI_RSS_FEEDS = [
    "https://news.google.com/rss/search?q=embedded+engineer+jobs+naukri+india&hl=en-IN&gl=IN",
    "https://news.google.com/rss/search?q=vlsi+firmware+hardware+jobs+naukri&hl=en-IN&gl=IN",
    "https://news.google.com/rss/search?q=fpga+electronics+engineer+naukri+india&hl=en-IN&gl=IN",
]


class NaukriScraper(BaseScraper):
    source = "Naukri"

    def scrape(self) -> list[dict]:
        jobs = []
        seen = set()
        fetch_count = 0
        skip_count = 0

        # Primary: scrape Naukri search pages
        for url in NAUKRI_URLS:
            try:
                resp = requests.get(url, headers=_HEADERS, timeout=20)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                # Naukri uses multiple layouts — try all known selectors
                cards = (
                    soup.select(".jobTuple, .job-post") or
                    soup.select("article.jobTupleHeader") or
                    soup.select(".cust-job-tuple") or
                    soup.select('[data-job-id]') or
                    soup.select(".srp-jobtuple-wrapper")
                )
                fetch_count += len(cards)

                for card in cards:
                    try:
                        title_el = (
                            card.select_one(".title a") or
                            card.select_one("a.title") or
                            card.select_one(".jobTitle a") or
                            card.select_one("a[href*='/job-listings-']")
                        )
                        company_el = (
                            card.select_one(".company-name") or
                            card.select_one(".companyInfo .company-name") or
                            card.select_one("a.comp-name")
                        )
                        location_el = (
                            card.select_one(".location") or
                            card.select_one(".locWdth") or
                            card.select_one("li.location span")
                        )
                        exp_el = (
                            card.select_one(".experience") or
                            card.select_one(".expwdth")
                        )

                        if not title_el:
                            skip_count += 1
                            continue

                        title = title_el.get_text(strip=True)
                        company = company_el.get_text(strip=True) if company_el else "Unknown"
                        location = location_el.get_text(strip=True) if location_el else "India"
                        eligibility = exp_el.get_text(strip=True) if exp_el else ""

                        href = title_el.get("href", "")
                        link = href if href.startswith("http") else f"https://www.naukri.com{href}"

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
                            location=location or "India",
                            link=link,
                            eligibility=eligibility,
                            skills=skills,
                        ))
                    except Exception as e:
                        logger.debug(f"Naukri card parse error: {e}")
                        skip_count += 1

            except requests.RequestException as e:
                logger.error(f"Naukri request failed [{url}]: {e}")
            except Exception as e:
                logger.error(f"Naukri scrape error [{url}]: {e}", exc_info=True)

        # Fallback: Google RSS if Naukri HTML scraping yielded nothing
        if not jobs:
            logger.info("Naukri HTML scraping yielded 0 jobs — trying Google RSS fallback")
            for feed_url in NAUKRI_RSS_FEEDS:
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
                    logger.error(f"Naukri RSS fallback error [{feed_url}]: {e}")

        logger.info(f"Naukri: fetched {fetch_count} entries → {len(jobs)} ECE jobs (skipped {skip_count})")
        return jobs
