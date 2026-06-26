import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from .database import SessionLocal
from .models import User, Job, UserJob, JobStatus
from .applier import Applier
from .matcher import Matcher

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username

    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if not user:
        user = User(telegram_id=user_id, username=username)
        db.add(user)
        db.commit()
        db.refresh(user)
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
    user = db.query(User).filter(User.telegram_id == user_id).first()

    if not user:
        await update.message.reply_text("Please run /start first.")
        db.close()
        return

    # Check if we're expecting a resume
    if len(text) > 100 and ("experience" in text.lower() or "skills" in text.lower() or "education" in text.lower()):
        user.resume_text = text
        db.commit()
        await update.message.reply_text("✅ Resume updated successfully! Now use /preferences if you haven't yet.")
        db.close()
        return

    # Simple parsing logic for preferences
    lines = text.split('\n')
    for line in lines:
        if ':' in line:
            key, val = line.split(':', 1)
            key = key.strip().lower()
            val = val.strip()

            if 'keyword' in key:
                user.keywords = val
            elif 'location' in key:
                user.location = val
            elif 'salary' in key:
                try:
                    user.salary_min = int(val)
                except: pass
            elif 'remote' in key:
                user.remote_only = val.lower() in ['yes', 'true', '1', 'sim']

    db.commit()
    await update.message.reply_text("✅ Preferences updated!")
    db.close()

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text("🔍 Searching for new jobs tailored to you... this might take a minute.")
    from .service import run_search_loop
    await run_search_loop(bot=context.bot, target_user_id=user_id)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split('_')
    action = data[0]
    user_job_id = int(data[1])

    db = SessionLocal()
    user_job = db.query(UserJob).filter(UserJob.id == user_job_id).first()

    if not user_job:
        await query.edit_message_text("Error: Job action not found.")
        db.close()
        return

    if action == "apply":
        # Actually trigger the applier
        matcher = Matcher()
        applier = Applier(matcher)

        success = await applier.apply_to_job(user_job.user, user_job)

        if success:
            user_job.status = JobStatus.APPLIED.value
            resp_text = f"🚀 Applied successfully! Tailored cover letter drafted:\n\n{user_job.cover_letter_draft}"
        else:
            resp_text = "⚠️ Failed to auto-apply. Please check the job link manually."
    elif action == "ignore":
        user_job.status = JobStatus.IGNORED.value
        resp_text = "❌ Ignored."
    elif action == "save":
        user_job.status = JobStatus.SAVED.value
        resp_text = "💾 Saved for later."
    elif action == "details":
        resp_text = f"📝 Description:\n\n{user_job.job.description[:1000]}..."

    db.commit()
    db.close()

    await query.message.reply_text(resp_text)

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
