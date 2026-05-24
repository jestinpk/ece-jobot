"""
Internshala scraper — BeautifulSoup HTML parsing.
Targets the ECE/Electronics internship/job listings.
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
    "Accept-Language": "en-US,en;q=0.9",
}

INTERNSHALA_URLS = [
    "https://internshala.com/internships/electronics-internship",
    "https://internshala.com/internships/embedded-systems-internship",
    "https://internshala.com/internships/vlsi-internship",
    "https://internshala.com/internships/iot-internship",
    "https://internshala.com/jobs/electronics-jobs",
    "https://internshala.com/jobs/embedded-systems-jobs",
]


class IntershalaScraper(BaseScraper):
    source = "Internshala"

    def scrape(self) -> list[dict]:
        jobs = []
        seen = set()

        for url in INTERNSHALA_URLS:
            try:
                resp = requests.get(url, headers=HEADERS, timeout=20)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                # Internshala listing cards
                cards = soup.select(".internship_meta, .individual_internship")
                if not cards:
                    # Fallback: try job cards
                    cards = soup.select('[data-internship_id], [data-job_id]')

                for card in cards:
                    try:
                        title_el = card.select_one(".profile a, .job-title a, h3 a")
                        company_el = card.select_one(".company_name a, .company-name")
                        location_el = card.select_one(".location_link, .location span, .job-location")
                        stipend_el = card.select_one(".stipend, .salary")

                        if not title_el:
                            continue

                        title = title_el.get_text(strip=True)
                        company = company_el.get_text(strip=True) if company_el else "Unknown"
                        location = location_el.get_text(strip=True) if location_el else "India"
                        stipend = stipend_el.get_text(strip=True) if stipend_el else ""

                        href = title_el.get("href", "")
                        link = f"https://internshala.com{href}" if href.startswith("/") else href

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
                            eligibility="B.E./B.Tech ECE/EEE/Instrumentation",
                            skills=skills,
                        ))
                    except Exception as e:
                        logger.debug(f"Internshala card parse error: {e}")

            except requests.RequestException as e:
                logger.error(f"Internshala request error ({url}): {e}")
            except Exception as e:
                logger.error(f"Internshala scrape error ({url}): {e}", exc_info=True)

        return jobs
