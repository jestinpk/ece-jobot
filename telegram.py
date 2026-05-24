"""
Telegram bot utility — formats and sends job alerts with inline buttons.
"""

import os
import logging
import requests

logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


class TelegramBot:
    def __init__(self):
        if not BOT_TOKEN or not CHAT_ID:
            raise EnvironmentError("BOT_TOKEN and CHAT_ID must be set as environment variables.")

    def _format_message(self, job: dict) -> str:
        company = job.get("company") or "Unknown"
        title = job.get("title") or "Unknown Role"
        location = job.get("location") or "Not specified"
        eligibility = job.get("eligibility", "")
        skills = job.get("skills", "")
        link = job.get("link", "#")

        lines = [
            "━━━━━━━━━━━━━━",
            "🔥 <b>ECE JOB ALERT</b>",
            "━━━━━━━━━━━━━━",
            f"🏢 <b>Company:</b>\n{self._esc(company)}",
            f"📌 <b>Role:</b>\n{self._esc(title)}",
        ]
        if eligibility:
            lines.append(f"🎓 <b>Eligibility:</b>\n{self._esc(eligibility)}")
        lines.append(f"📍 <b>Location:</b>\n{self._esc(location)}")
        if skills:
            lines.append(f"🛠 <b>Skills:</b>\n{self._esc(skills)}")
        lines += [
            f"🔗 <b>Apply Now:</b>\n{link}",
            "#ECE #Embedded #Jobs",
            "━━━━━━━━━━━━━━",
        ]
        return "\n".join(lines)

    @staticmethod
    def _esc(text: str) -> str:
        """Escape HTML special characters."""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))

    def post_job(self, job: dict) -> bool:
        message = self._format_message(job)
        payload = {
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
            "reply_markup": {
                "inline_keyboard": [[
                    {"text": "🚀 Apply Now", "url": job.get("link", "#")},
                    {"text": "🔍 More ECE Jobs", "url": "https://www.linkedin.com/jobs/search/?keywords=ECE+embedded"}
                ]]
            }
        }
        try:
            resp = requests.post(f"{TELEGRAM_API}/sendMessage", json=payload, timeout=15)
            resp.raise_for_status()
            logger.info(f"Posted: {job.get('title')} @ {job.get('company')}")
            return True
        except requests.RequestException as e:
            logger.error(f"Telegram post failed: {e}")
            return False

    def send_text(self, text: str):
        """Send a plain notification message."""
        requests.post(f"{TELEGRAM_API}/sendMessage", json={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        }, timeout=10)
