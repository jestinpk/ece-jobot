"""
Cutshort scraper — India startup/tech job platform, ECE roles.
"""

import logging
import requests
from bs4 import BeautifulSoup
from utils.filters import BaseScraper, is_ece_job, extract_skills, HEADERS

logger = logging.getLogger(__name__)

_HEADERS = {**HEADERS, "Referer": "https://cutshort.io/"}

CUTSHORT_URLS = [
    "https://cutshort.io/jobs/embedded-engineer",
    "https://cutshort.io/jobs/firmware-engineer",
    "https://cutshort.io/jobs/electronics-engineer",
    "https://cutshort.io/jobs/hardware-engineer",
    "https://cutshort.io/jobs/iot-engineer",
    "https://cutshort.io/jobs/vlsi-engineer",
]


class CutshortScraper(BaseScraper):
    source = "Cutshort"

    def scrape(self) -> list[dict]:
        jobs = []
        seen = set()
        fetch_count = 0
        skip_count = 0

        for url in CUTSHORT_URLS:
            try:
                resp = requests.get(url, headers=_HEADERS, timeout=20)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                cards = (
                    soup.select(".job-card") or
                    soup.select("[class*='JobCard']") or
                    soup.select(".job-list-item") or
                    soup.select("article[class*='job']")
                )
                fetch_count += len(cards)

                for card in cards:
                    try:
                        title_el = (
                            card.select_one("h2 a") or
                            card.select_one("h3 a") or
                            card.select_one(".job-title a") or
                            card.select_one("a[href*='/jobs/']")
                        )
                        company_el = (
                            card.select_one(".company-name") or
                            card.select_one("[class*='company']")
                        )
                        location_el = (
                            card.select_one(".location") or
                            card.select_one("[class*='location']")
                        )
                        skills_el = card.select(".skill-tag, .tag, [class*='skill']")

                        if not title_el:
                            skip_count += 1
                            continue

                        title = title_el.get_text(strip=True)
                        company = company_el.get_text(strip=True) if company_el else "Unknown"
                        location = location_el.get_text(strip=True) if location_el else "India"
                        raw_skills = ", ".join(s.get_text(strip=True) for s in skills_el) if skills_el else ""

                        href = title_el.get("href", "")
                        link = f"https://cutshort.io{href}" if href.startswith("/") else href

                        if not link or link in seen:
                            skip_count += 1
                            continue
                        seen.add(link)

                        if not is_ece_job(title, raw_skills):
                            skip_count += 1
                            continue

                        skills = raw_skills or extract_skills(title)
                        jobs.append(self.make_job(
                            title=title,
                            company=company,
                            location=location or "India",
                            link=link,
                            skills=skills,
                        ))
                    except Exception as e:
                        logger.debug(f"Cutshort card parse error: {e}")
                        skip_count += 1

            except requests.RequestException as e:
                logger.error(f"Cutshort request failed [{url}]: {e}")
            except Exception as e:
                logger.error(f"Cutshort scrape error [{url}]: {e}", exc_info=True)

        logger.info(f"Cutshort: fetched {fetch_count} cards → {len(jobs)} ECE jobs (skipped {skip_count})")
        return jobs
