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


    def post_daily_digest(self, jobs: list, total_in_db: int) -> bool:
        """Send a daily digest card summarising the best recent jobs."""
        if not jobs:
            # No jobs at all in DB yet — send a simple status ping
            text = (
                "📡 <b>ECE Job Bot — Daily Check-in</b>\n"
                "━━━━━━━━━━━━━━\n"
                "No new ECE jobs found in the last 24 hours.\n"
                "The bot is running and will alert you the moment new jobs appear! 🔔\n"
                "━━━━━━━━━━━━━━\n"
                "#ECE #JobAlert #India"
            )
            payload = {
                "chat_id": CHAT_ID,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }
        else:
            lines = [
                "━━━━━━━━━━━━━━",
                "📋 <b>ECE JOBS — DAILY DIGEST</b>",
                f"🗓 Top {len(jobs)} jobs from the last 24 hours",
                "━━━━━━━━━━━━━━",
            ]
            for i, job in enumerate(jobs, 1):
                title   = self._esc(job.get("title", "Unknown Role"))
                company = self._esc(job.get("company", "Unknown"))
                loc     = self._esc(job.get("location", "India"))
                link    = job.get("link", "#")
                lines.append(
                    f"{i}. <b>{title}</b>\n"
                    f"   🏢 {company} | 📍 {loc}\n"
                    f"   🔗 <a href='{link}'>Apply Now</a>"
                )
            lines += [
                "━━━━━━━━━━━━━━",
                f"📊 <i>{total_in_db} total jobs tracked so far</i>",
                "#ECE #Embedded #Jobs #India #DailyDigest",
                "━━━━━━━━━━━━━━",
            ]
            text = "\n".join(lines)
            payload = {
                "chat_id": CHAT_ID,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
                "reply_markup": {
                    "inline_keyboard": [[
                        {"text": "🔍 Search ECE Jobs", "url": "https://in.indeed.com/jobs?q=embedded+engineer"},
                        {"text": "📢 Share Channel", "url": "https://t.me/share/url?url=ECE+Job+Alerts"}
                    ]]
                }
            }

        try:
            resp = requests.post(f"{TELEGRAM_API}/sendMessage", json=payload, timeout=15)
            resp.raise_for_status()
            logger.info(f"Daily digest sent ({len(jobs)} jobs)")
            return True
        except requests.RequestException as e:
            logger.error(f"Digest post failed: {e}")
            return False
