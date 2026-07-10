import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from ...infrastructure.database.connection import SessionLocal
from ...infrastructure.database.repositories import SQLUserRepository, SQLJobRepository, SQLUserJobRepository
from ...infrastructure.appliers.playwright import PlaywrightApplier
from ...infrastructure.matchers.gemini import GeminiMatcher
from ...application.use_cases import (
    RegisterOrGetUserUseCase,
    UpdateResumeUseCase,
    UpdatePreferencesUseCase,
    SearchAndMatchJobsUseCase,
    ApplyToJobUseCase,
    IgnoreJobUseCase,
    SaveJobUseCase
)

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username

    db = SessionLocal()
    try:
        user_repo = SQLUserRepository(db)
        use_case = RegisterOrGetUserUseCase(user_repo)
        use_case.execute(user_id, username)
    finally:
        db.close()

    await update.message.reply_text(
        "👋 Welcome to Smart Job Agent!\n\n"
        "I'll help you find and apply to jobs automatically.\n\n"
        "1️⃣ Use /resume to upload your CV/Resume text.\n"
        "2️⃣ Use /preferences to set your job criteria.\n"
        "3️⃣ Use /search to trigger a search now."
    )

async def set_resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please send your resume or CV as a text message.")

async def set_preferences(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Please send your preferences in the format:\n"
        "Keywords: Python, Go\n"
        "Location: Remote\n"
        "Salary: 100000\n"
        "Remote: Yes"
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    db = SessionLocal()
    try:
        user_repo = SQLUserRepository(db)
        user = user_repo.get_by_telegram_id(user_id)

        if not user:
            await update.message.reply_text("Please run /start first.")
            return

        # Check if we're expecting a resume
        if len(text) > 100 and ("experience" in text.lower() or "skills" in text.lower() or "education" in text.lower()):
            use_case = UpdateResumeUseCase(user_repo)
            use_case.execute(user_id, text)
            await update.message.reply_text("✅ Resume updated successfully! Now use /preferences if you haven't yet.")
            return

        # Simple parsing logic for preferences
        lines = text.split('\n')
        preferences_data = {}
        for line in lines:
            if ':' in line:
                key, val = line.split(':', 1)
                key = key.strip().lower()
                val = val.strip()

                if 'keyword' in key:
                    preferences_data["keywords"] = val
                elif 'location' in key:
                    preferences_data["location"] = val
                elif 'salary' in key:
                    try:
                        preferences_data["salary_min"] = int(val)
                    except: pass
                elif 'remote' in key:
                    preferences_data["remote_only"] = val.lower() in ['yes', 'true', '1', 'sim']

        if preferences_data:
            use_case = UpdatePreferencesUseCase(user_repo)
            use_case.execute(user_id, preferences_data)
            await update.message.reply_text("✅ Preferences updated!")
        else:
            await update.message.reply_text("Could not parse preferences. Please follow the required /preferences format.")
    finally:
        db.close()

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text("🔍 Searching for new jobs tailored to you... this might take a minute.")

    # We delay load scraper to avoid cyclic imports
    from ...infrastructure.scrapers.remote_ok import RemoteOkScraper

    db = SessionLocal()
    try:
        user_repo = SQLUserRepository(db)
        job_repo = SQLJobRepository(db)
        user_job_repo = SQLUserJobRepository(db)
        scraper = RemoteOkScraper()
        matcher = GeminiMatcher()

        use_case = SearchAndMatchJobsUseCase(user_repo, job_repo, user_job_repo, scraper, matcher)

        async def on_match_found(telegram_id, user_job):
            await send_job_alert(context.bot, telegram_id, user_job)

        await use_case.execute(target_telegram_id=user_id, on_match_found=on_match_found)
    finally:
        db.close()

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split('_')
    action = data[0]
    user_job_id = int(data[1])

    db = SessionLocal()
    try:
        user_job_repo = SQLUserJobRepository(db)
        user_job = user_job_repo.get_by_id(user_job_id)

        if not user_job:
            await query.edit_message_text("Error: Job action not found.")
            return

        resp_text = ""
        if action == "apply":
            applier = PlaywrightApplier()
            use_case = ApplyToJobUseCase(user_job_repo, applier)
            success, updated_user_job = await use_case.execute(user_job_id)

            if success:
                resp_text = f"🚀 Applied successfully! Tailored cover letter drafted:\n\n{updated_user_job.cover_letter_draft}"
            else:
                resp_text = "⚠️ Failed to auto-apply. Please check the job link manually."
        elif action == "ignore":
            use_case = IgnoreJobUseCase(user_job_repo)
            use_case.execute(user_job_id)
            resp_text = "❌ Ignored."
        elif action == "save":
            use_case = SaveJobUseCase(user_job_repo)
            use_case.execute(user_job_id)
            resp_text = "💾 Saved for later."
        elif action == "details":
            resp_text = f"📝 Description:\n\n{user_job.job.description[:1000]}..."

        await query.message.reply_text(resp_text)
    finally:
        db.close()

def get_job_keyboard(user_job_id: int):
    keyboard = [
        [
            InlineKeyboardButton("📄 Details", callback_data=f"details_{user_job_id}"),
            InlineKeyboardButton("🚀 Apply", callback_data=f"apply_{user_job_id}"),
        ],
        [
            InlineKeyboardButton("💾 Save", callback_data=f"save_{user_job_id}"),
            InlineKeyboardButton("❌ Ignore", callback_data=f"ignore_{user_job_id}"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def send_job_alert(bot, chat_id, user_job):
    job = user_job.job
    message = (
        f"🎯 *Match Score: {user_job.relevance_score:.0f}%*\n\n"
        f"📌 *{job.title}*\n"
        f"🏢 {job.company}\n"
        f"📍 {job.location}\n"
        f"💰 {job.salary}\n\n"
        f"💡 *Why it matches:* {user_job.matching_reason}\n\n"
        f"🔗 [Link to Apply]({job.link})"
    )
    await bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode="Markdown",
        reply_markup=get_job_keyboard(user_job.id)
    )
