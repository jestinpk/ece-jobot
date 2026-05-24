"""
RemoteOK scraper — FALLBACK ONLY.
Only used when Indian primary sources return fewer than MIN_INDIAN_JOBS total jobs.
Uses public JSON API: https://remoteok.com/api
"""

import logging
import requests
from utils.filters import BaseScraper, is_ece_job, extract_skills, HEADERS

logger = logging.getLogger(__name__)

REMOTEOK_API = "https://remoteok.com/api"
MIN_INDIAN_JOBS = 5  # Only activate if primary sources return fewer than this

_HEADERS = {**HEADERS, "User-Agent": "ECEJobBot/2.0 (job aggregator; India focus)"}


class RemoteOKScraper(BaseScraper):
    source = "RemoteOK"
    is_fallback = True  # Flag for bot.py to treat as fallback

    def scrape(self) -> list[dict]:
        jobs = []
        fetch_count = 0
        skip_count = 0

        try:
            resp = requests.get(REMOTEOK_API, headers=_HEADERS, timeout=20)
            resp.raise_for_status()
            data = resp.json()

            for item in data[1:]:  # First item is legal notice
                if not isinstance(item, dict):
                    continue
                fetch_count += 1

                title = item.get("position", "")
                company = item.get("company", "")
                location = item.get("location", "Remote")
                tags = " ".join(item.get("tags", []))
                description = item.get("description", "")
                combined = f"{title} {tags} {description}"

                if not is_ece_job(title, combined):
                    skip_count += 1
                    continue

                link = item.get("url") or f"https://remoteok.com/remote-jobs/{item.get('id', '')}"
                skills = extract_skills(combined)
                jobs.append(self.make_job(
                    title=title,
                    company=company,
                    location=location or "Remote",
                    link=link,
                    skills=skills,
                    description=description,
                ))

        except Exception as e:
            logger.error(f"RemoteOK scrape error: {e}", exc_info=True)

        logger.info(f"RemoteOK (fallback): fetched {fetch_count} → {len(jobs)} ECE jobs (skipped {skip_count})")
        return jobs
