# 🤖 ECE Job Alert Bot

A Telegram bot that automatically scrapes ECE (Electronics & Communication Engineering) jobs from multiple sources and posts them to your Telegram channel every 10 minutes.

---

## 📦 Project Structure

```
ece_job_bot/
├── bot.py                  # Main entry point (local continuous mode)
├── run_once.py             # Single-cycle runner (for GitHub Actions)
├── requirements.txt
├── .env.example
├── .gitignore
├── scrapers/
│   ├── __init__.py
│   ├── remoteok.py         # RemoteOK JSON API
│   ├── indeed.py           # Indeed RSS feeds
│   ├── internshala.py      # Internshala HTML scraper
│   └── freshersworld.py    # Freshersworld HTML scraper
├── utils/
│   ├── __init__.py
│   ├── database.py         # SQLite duplicate prevention
│   ├── filters.py          # ECE keyword filtering + base scraper
│   └── telegram.py         # Telegram message formatter + poster
├── data/                   # Auto-created; holds jobs.db
└── .github/
    └── workflows/
        └── bot.yml         # GitHub Actions cron (every 10 min)
```

---

## 🚀 Setup

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/ece-job-bot.git
cd ece-job-bot
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Create a Telegram Bot
1. Open Telegram and message [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the prompts
3. Copy the **Bot Token**

### 4. Get your Chat ID
- For a **channel**: Add the bot as admin, then send a message to the channel. Use:
  ```
  https://api.telegram.org/bot<BOT_TOKEN>/getUpdates
  ```
  Find `"chat":{"id":...}` in the response. Channel IDs start with `-100`.
- For a **group**: Same process — add bot to group, use `/getUpdates`.
- For **yourself**: Message [@userinfobot](https://t.me/userinfobot).

### 5. Configure environment
```bash
cp .env.example .env
# Edit .env and fill in BOT_TOKEN and CHAT_ID
```

### 6. Run locally
```bash
# Continuous mode (runs every 10 minutes)
python bot.py

# Single cycle (for testing)
python run_once.py
```

---

## ☁️ GitHub Actions Deployment (Free, Always-On)

### 1. Push to GitHub
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

### 2. Add Secrets
Go to your repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Secret Name | Value |
|-------------|-------|
| `BOT_TOKEN` | Your Telegram bot token |
| `CHAT_ID`   | Your channel/group/user chat ID |

### 3. Enable Actions
Go to **Actions** tab → enable workflows if prompted.

The bot will now run **every 10 minutes** automatically. The SQLite database is cached between runs to prevent duplicate posts.

---

## 📢 Sample Telegram Output

```
━━━━━━━━━━━━━━
🔥 ECE JOB ALERT
━━━━━━━━━━━━━━
🏢 Company:
Texas Instruments

📌 Role:
Embedded Systems Engineer

🎓 Eligibility:
B.E./B.Tech ECE/EEE/Instrumentation

📍 Location:
Bengaluru, India

🛠 Skills:
EMBEDDED, FIRMWARE, RTOS, MICROCONTROLLER

🔗 Apply Now:
https://example.com/apply

#ECE #Embedded #Jobs
━━━━━━━━━━━━━━
[🚀 Apply Now] [🔍 More ECE Jobs]
```

---

## 🔍 ECE Keywords Filtered

`electronics` `embedded` `vlsi` `iot` `pcb` `hardware` `firmware` `telecom` `robotics` `fpga` `rtos` `microcontroller` `signal processing` `verilog` `vhdl` `circuit` `rf` `antenna` `semiconductor`

---

## 🗄️ Sources

| Source | Method |
|--------|--------|
| **RemoteOK** | Public JSON API |
| **Indeed** | RSS Feeds |
| **Internshala** | HTML scraping (BeautifulSoup) |
| **Freshersworld** | HTML scraping (BeautifulSoup) |

---

## ⚙️ Features

- ✅ Duplicate prevention via SQLite + MD5 URL hashing
- ✅ ECE keyword filtering (10+ keywords)
- ✅ Telegram inline buttons (Apply Now + Search More)
- ✅ HTML-formatted messages
- ✅ Optional fields (eligibility, skills hidden if unavailable)
- ✅ GitHub Actions free deployment with cron scheduling
- ✅ Database caching between GitHub Actions runs
- ✅ Modular scraper architecture (easy to add new sources)
- ✅ Logging to file + console
- ✅ Environment variable configuration

---

## 🛠️ Adding a New Scraper

1. Create `scrapers/mysource.py`
2. Extend `BaseScraper` from `utils.filters`
3. Implement `scrape()` returning a list of job dicts
4. Import and add to the scrapers list in `bot.py` and `run_once.py`

```python
from utils.filters import BaseScraper, is_ece_job, extract_skills

class MySourceScraper(BaseScraper):
    source = "MySource"

    def scrape(self) -> list[dict]:
        jobs = []
        # ... your scraping logic ...
        jobs.append(self.make_job(
            title="Embedded Engineer",
            company="Acme Corp",
            location="Mumbai",
            link="https://example.com/job/123",
            eligibility="B.Tech ECE",
            skills="EMBEDDED, RTOS",
        ))
        return jobs
```

---

## 📄 License

MIT License — free to use and modify.
