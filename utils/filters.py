"""
ECE job keyword filtering, India-only filtering, and base scraper class.
"""

import logging

logger = logging.getLogger(__name__)

# ── ECE keyword list (expanded) ───────────────────────────────────────────────
ECE_KEYWORDS = [
    "electronics", "embedded", "vlsi", "iot", "pcb",
    "hardware", "firmware", "telecom", "robotics", "fpga",
    "microcontroller", "stm32", "avr", "arduino", "raspberry pi",
    "verilog", "rtl", "asic", "semiconductor", "embedded linux",
    "device driver", "bare metal", "rtos", "rf", "antenna",
    "signal processing", "vhdl", "circuit", "schematic",
]

# ── India location keywords ───────────────────────────────────────────────────
INDIA_KEYWORDS = [
    "india", "bangalore", "bengaluru", "hyderabad", "pune",
    "chennai", "kochi", "kerala", "noida", "gurgaon", "gurugram",
    "delhi", "mumbai", "ahmedabad", "kolkata", "coimbatore",
    "mysuru", "mysore", "jaipur", "bhubaneswar", "trichy",
    "vizag", "visakhapatnam", "chandigarh", "lucknow",
]

# Keywords that clearly indicate non-India jobs
NON_INDIA_KEYWORDS = [
    "usa", "united states", "us only", "canada", "uk only",
    "europe", "germany", "france", "australia", "singapore",
    "worldwide", "global remote", "anywhere in the world",
]

# Standard browser headers for all requests
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def is_ece_job(title: str, description: str = "") -> bool:
    """Return True if title or description matches ECE keywords."""
    combined = f"{title} {description}".lower()
    return any(kw in combined for kw in ECE_KEYWORDS)


def is_indian_job(job: dict) -> bool:
    """
    Return True if job is likely based in India.
    Checks location, title, description, and company fields.
    Rejects jobs with explicit non-India indicators.
    """
    combined = " ".join([
        job.get("location", ""),
        job.get("title", ""),
        job.get("description", ""),
        job.get("company", ""),
    ]).lower()

    # Reject explicit non-India jobs
    if any(kw in combined for kw in NON_INDIA_KEYWORDS):
        return False

    # Accept if any India keyword found
    if any(kw in combined for kw in INDIA_KEYWORDS):
        return True

    # For sources that are India-specific by nature, allow through
    if job.get("source") in ("Internshala", "Freshersworld", "Naukri",
                              "Instahyre", "Cutshort", "GoogleRSS"):
        return True

    return False


def extract_skills(text: str) -> str:
    """Extract matching ECE skills from text."""
    found = []
    text_lower = text.lower()
    for kw in ECE_KEYWORDS:
        if kw in text_lower and kw.upper() not in found:
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
            "location": location.strip() if location else "India",
            "link": link.strip(),
            "eligibility": eligibility.strip(),
            "skills": skills.strip(),
            "description": description[:300] if description else "",
            "source": self.source,
        }
