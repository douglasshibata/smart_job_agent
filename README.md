# 🤖 Smart Job Agent Telegram Bot

An AI-powered Telegram bot that automates job search, matching, and application preparation.

## 🚀 Features

- **Automated Search**: Polls job boards like RemoteOK for new opportunities.
- **AI Matching**: Uses Gemini (via LangChain) to score jobs against your resume/preferences.
- **Tailored Materials**: Automatically drafts personalized cover letters for each job.
- **Interactive Interface**: Receive alerts directly on Telegram with "Apply", "Save", and "Ignore" actions.
- **Persistence**: Tracks your search history and application status in a local database.

## 🛠️ Setup

1. **Clone the repository** (if you haven't already).
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```
3. **Configure Environment**:
   Copy `.env.example` to `.env` and fill in:
   - `TELEGRAM_TOKEN`: From [@BotFather](https://t.me/botfather).
   - `GOOGLE_API_KEY`: For Gemini AI.
   - `DATABASE_URL`: Defaults to local SQLite.

4. **Run the application**:
   ```bash
   python -m smart_job_agent.main
   ```

## 🤖 Bot Commands

- `/start` - Initialize your account.
- `/preferences` - Instructions to set your job criteria.
- `/search` - Manually trigger a search for new jobs.

## 🏗️ Architecture

- `main.py`: Entry point, integrates FastAPI, Bot, and Scheduler.
- `bot.py`: Telegram interface and command handlers.
- `scraper.py`: Logic to fetch jobs from external sources.
- `matcher.py`: AI logic for relevance scoring and cover letter drafting.
- `applier.py`: Playwright-based browser automation skeleton for auto-applying.
- `models.py` & `database.py`: SQLAlchemy ORM and database configuration.

## 🧪 Testing

Run the test suite:
```bash
export PYTHONPATH=$PYTHONPATH:.
python3 -m pytest smart_job_agent/tests/
```
