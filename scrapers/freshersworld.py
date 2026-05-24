"""
Freshersworld scraper — ECE fresher job listings in India.
"""

import logging
import requests
from bs4 import BeautifulSoup
from utils.filters import BaseScraper, is_ece_job, extract_skills, HEADERS

logger = logging.getLogger(__name__)

_HEADERS = {**HEADERS, "Referer": "https://www.freshersworld.com/"}

FRESHERSWORLD_URLS = [
    "https://www.freshersworld.com/jobs/category/ece-job-vacancies",
    "https://www.freshersworld.com/jobs/jobsearch/embedded-systems-engineer-jobs",
    "https://www.freshersworld.com/jobs/jobsearch/VLSI-engineer-jobs",
    "https://www.freshersworld.com/jobs/jobsearch/hardware-engineer-jobs",
    "https://www.freshersworld.com/jobs/jobsearch/firmware-engineer-jobs",
    "https://www.freshersworld.com/jobs/jobsearch/IoT-engineer-jobs",
    "https://www.freshersworld.com/jobs/jobsearch/PCB-design-engineer-jobs",
    "https://www.freshersworld.com/jobs/jobsearch/electronics-engineer-jobs",
]


class FreshersworldScraper(BaseScraper):
    source = "Freshersworld"

    def scrape(self) -> list[dict]:
        jobs = []
        seen = set()
        fetch_count = 0
        skip_count = 0

        for url in FRESHERSWORLD_URLS:
            try:
                resp = requests.get(url, headers=_HEADERS, timeout=20)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                # Try multiple card selectors
                cards = (
                    soup.select(".job-container") or
                    soup.select(".jobs-list li") or
                    soup.select(".job-box") or
                    soup.select("article.job") or
                    soup.select(".listing-item") or
                    soup.select(".jobs_tabpanel .container-box")
                )
                fetch_count += len(cards)

                for card in cards:
                    try:
                        title_el = (
                            card.select_one("h3 a") or
                            card.select_one(".job-title a") or
                            card.select_one("a.job-link") or
                            card.select_one("h2 a") or
                            card.select_one("a[href*='/jobs/']")
                        )
                        company_el = (
                            card.select_one(".company-name") or
                            card.select_one(".employer") or
                            card.select_one(".org-name") or
                            card.select_one(".company_name")
                        )
                        location_el = (
                            card.select_one(".location") or
                            card.select_one(".job-location") or
                            card.select_one(".city")
                        )
                        exp_el = (
                            card.select_one(".experience") or
                            card.select_one(".eligibility") or
                            card.select_one(".exp")
                        )

                        if not title_el:
                            skip_count += 1
                            continue

                        title = title_el.get_text(strip=True)
                        company = company_el.get_text(strip=True) if company_el else "Unknown"
                        location = location_el.get_text(strip=True) if location_el else "India"
                        eligibility = exp_el.get_text(strip=True) if exp_el else "Freshers / 0-2 years"

                        href = title_el.get("href", "")
                        link = href if href.startswith("http") else f"https://www.freshersworld.com{href}"

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
                        logger.debug(f"Freshersworld card parse error: {e}")
                        skip_count += 1

            except requests.RequestException as e:
                logger.error(f"Freshersworld request failed [{url}]: {e}")
            except Exception as e:
                logger.error(f"Freshersworld scrape error [{url}]: {e}", exc_info=True)

        logger.info(f"Freshersworld: fetched {fetch_count} cards → {len(jobs)} ECE jobs (skipped {skip_count})")
        return jobs
