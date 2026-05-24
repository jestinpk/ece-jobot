"""
ECE job keyword filtering and base scraper class.
"""

import logging
import re

logger = logging.getLogger(__name__)

ECE_KEYWORDS = [
    "electronics", "embedded", "vlsi", "iot", "pcb",
    "hardware", "firmware", "telecom", "robotics", "fpga",
    "rtos", "microcontroller", "arduino", "raspberry pi",
    "signal processing", "verilog", "vhdl", "circuit",
    "schematic", "rf", "antenna", "semiconductor",
]


def is_ece_job(title: str, description: str = "") -> bool:
    """Return True if title or description matches ECE keywords."""
    combined = f"{title} {description}".lower()
    return any(kw in combined for kw in ECE_KEYWORDS)


def extract_skills(text: str) -> str:
    """Extract matching ECE skills from text."""
    found = []
    text_lower = text.lower()
    for kw in ECE_KEYWORDS:
        if kw in text_lower:
            found.append(kw.upper())
    return ", ".join(found[:8]) if found else ""


class BaseScraper:
    source = "Unknown"

    def scrape(self) -> list[dict]:
        raise NotImplementedError

    def make_job(self, title, company, location, link,
                 eligibility="", skills="", description="") -> dict:
        if not skills and description:
            skills = extract_skills(description)
        return {
            "title": title.strip(),
            "company": company.strip(),
            "location": location.strip() if location else "Remote / Not specified",
            "link": link.strip(),
            "eligibility": eligibility.strip(),
            "skills": skills.strip(),
            "source": self.source,
        }
