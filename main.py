import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

from .infrastructure.database.connection import engine, Base
from .infrastructure.telegram.bot import start, set_resume, set_preferences, handle_text, search_command, button_callback
from .service import run_search_loop

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

bot_app = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Bot
    global bot_app
    token = os.getenv("TELEGRAM_TOKEN")
    if token:
        bot_app = ApplicationBuilder().token(token).build()
        bot_app.add_handler(CommandHandler("start", start))
        bot_app.add_handler(CommandHandler("resume", set_resume))
        bot_app.add_handler(CommandHandler("preferences", set_preferences))
        bot_app.add_handler(CommandHandler("search", search_command))
        bot_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
        bot_app.add_handler(CallbackQueryHandler(button_callback))

        await bot_app.initialize()
        await bot_app.start()
        await bot_app.updater.start_polling()
        logger.info("Telegram Bot started.")
    else:
        logger.warning("TELEGRAM_TOKEN not set. Bot will not start.")

    # Initialize Scheduler
    scheduler = AsyncIOScheduler()
    interval = int(os.getenv("SEARCH_INTERVAL_HOURS", 6))

    # Wrap search loop to pass the bot instance
    async def scheduled_search():
        if bot_app:
            await run_search_loop(bot=bot_app.bot)
        else:
            await run_search_loop()

    scheduler.add_job(scheduled_search, 'interval', hours=interval)
    scheduler.start()
    logger.info(f"Scheduler started (interval: {interval}h).")

    yield

    # Shutdown
    if bot_app:
        await bot_app.updater.stop()
        await bot_app.stop()
        await bot_app.shutdown()
    if scheduler.running:
        scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
