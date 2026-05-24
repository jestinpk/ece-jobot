"""
Instahyre scraper — curated India tech jobs, ECE/hardware roles.
"""

import logging
import requests
from bs4 import BeautifulSoup
from utils.filters import BaseScraper, is_ece_job, extract_skills, HEADERS

logger = logging.getLogger(__name__)

_HEADERS = {**HEADERS, "Referer": "https://www.instahyre.com/"}

INSTAHYRE_URLS = [
    "https://www.instahyre.com/jobs/embedded-engineer/",
    "https://www.instahyre.com/jobs/firmware-engineer/",
    "https://www.instahyre.com/jobs/electronics-engineer/",
    "https://www.instahyre.com/jobs/hardware-engineer/",
    "https://www.instahyre.com/jobs/vlsi-engineer/",
    "https://www.instahyre.com/jobs/iot-engineer/",
]


class InstaHyreScraper(BaseScraper):
    source = "Instahyre"

    def scrape(self) -> list[dict]:
        jobs = []
        seen = set()
        fetch_count = 0
        skip_count = 0

        for url in INSTAHYRE_URLS:
            try:
                resp = requests.get(url, headers=_HEADERS, timeout=20)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                cards = (
                    soup.select(".job-card") or
                    soup.select(".opportunity-card") or
                    soup.select("[class*='JobCard']") or
                    soup.select(".jobs-list .item")
                )
                fetch_count += len(cards)

                for card in cards:
                    try:
                        title_el = (
                            card.select_one(".job-title") or
                            card.select_one("h2 a") or
                            card.select_one("h3 a") or
                            card.select_one("a[href*='/candidate/opportunities/']")
                        )
                        company_el = (
                            card.select_one(".company-name") or
                            card.select_one(".employer-name")
                        )
                        location_el = (
                            card.select_one(".location") or
                            card.select_one(".job-location")
                        )

                        if not title_el:
                            skip_count += 1
                            continue

                        title = title_el.get_text(strip=True)
                        company = company_el.get_text(strip=True) if company_el else "Unknown"
                        location = location_el.get_text(strip=True) if location_el else "India"

                        href = title_el.get("href", "")
                        link = f"https://www.instahyre.com{href}" if href.startswith("/") else href

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
                            skills=skills,
                        ))
                    except Exception as e:
                        logger.debug(f"Instahyre card parse error: {e}")
                        skip_count += 1

            except requests.RequestException as e:
                logger.error(f"Instahyre request failed [{url}]: {e}")
            except Exception as e:
                logger.error(f"Instahyre scrape error [{url}]: {e}", exc_info=True)

        logger.info(f"Instahyre: fetched {fetch_count} cards → {len(jobs)} ECE jobs (skipped {skip_count})")
        return jobs
