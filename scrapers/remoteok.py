"""
RemoteOK scraper — uses their public JSON API.
https://remoteok.com/api
"""

import logging
import requests
from utils.filters import BaseScraper, is_ece_job, extract_skills

logger = logging.getLogger(__name__)

REMOTEOK_API = "https://remoteok.com/api"
HEADERS = {"User-Agent": "ECEJobBot/1.0 (job aggregator)"}


class RemoteOKScraper(BaseScraper):
    source = "RemoteOK"

    def scrape(self) -> list[dict]:
        jobs = []
        try:
            resp = requests.get(REMOTEOK_API, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            # First item is a legal notice dict, skip it
            for item in data[1:]:
                if not isinstance(item, dict):
                    continue
                title = item.get("position", "")
                company = item.get("company", "")
                location = item.get("location", "Remote")
                tags = " ".join(item.get("tags", []))
                description = item.get("description", "")
                combined = f"{title} {tags} {description}"

                if not is_ece_job(title, combined):
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
        return jobs
