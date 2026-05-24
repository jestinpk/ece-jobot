"""
Freshersworld scraper — BeautifulSoup HTML parsing.
Targets ECE fresher job listings.
"""

import logging
import requests
from bs4 import BeautifulSoup
from utils.filters import BaseScraper, is_ece_job, extract_skills

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.freshersworld.com/",
}

FRESHERSWORLD_URLS = [
    "https://www.freshersworld.com/jobs/jobsearch/ECE-jobs-for-freshers",
    "https://www.freshersworld.com/jobs/jobsearch/embedded-systems-engineer-jobs",
    "https://www.freshersworld.com/jobs/jobsearch/VLSI-engineer-jobs",
    "https://www.freshersworld.com/jobs/jobsearch/hardware-engineer-jobs",
    "https://www.freshersworld.com/jobs/jobsearch/firmware-engineer-jobs",
    "https://www.freshersworld.com/jobs/jobsearch/IoT-engineer-jobs",
]


class FreshersworldScraper(BaseScraper):
    source = "Freshersworld"

    def scrape(self) -> list[dict]:
        jobs = []
        seen = set()

        for url in FRESHERSWORLD_URLS:
            try:
                resp = requests.get(url, headers=HEADERS, timeout=20)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                # Freshersworld job listing cards
                cards = soup.select(".job-container, .jobs-list li, .job-box")
                if not cards:
                    cards = soup.select("article.job, .listing-item")

                for card in cards:
                    try:
                        title_el = (
                            card.select_one("h3 a") or
                            card.select_one(".job-title a") or
                            card.select_one("a.job-link") or
                            card.select_one("h2 a")
                        )
                        company_el = (
                            card.select_one(".company-name") or
                            card.select_one(".employer") or
                            card.select_one(".org-name")
                        )
                        location_el = (
                            card.select_one(".location") or
                            card.select_one(".job-location")
                        )
                        exp_el = (
                            card.select_one(".experience") or
                            card.select_one(".eligibility")
                        )

                        if not title_el:
                            continue

                        title = title_el.get_text(strip=True)
                        company = company_el.get_text(strip=True) if company_el else "Unknown"
                        location = location_el.get_text(strip=True) if location_el else "India"
                        eligibility = exp_el.get_text(strip=True) if exp_el else "Freshers / 0-2 years"

                        href = title_el.get("href", "")
                        link = href if href.startswith("http") else f"https://www.freshersworld.com{href}"

                        if not link or link in seen:
                            continue
                        seen.add(link)

                        if not is_ece_job(title, ""):
                            continue

                        skills = extract_skills(title)
                        jobs.append(self.make_job(
                            title=title,
                            company=company,
                            location=location,
                            link=link,
                            eligibility=eligibility,
                            skills=skills,
                        ))
                    except Exception as e:
                        logger.debug(f"Freshersworld card parse error: {e}")

            except requests.RequestException as e:
                logger.error(f"Freshersworld request error ({url}): {e}")
            except Exception as e:
                logger.error(f"Freshersworld scrape error ({url}): {e}", exc_info=True)

        return jobs
