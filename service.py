import logging
from .infrastructure.database.connection import SessionLocal
from .infrastructure.database.repositories import SQLUserRepository, SQLJobRepository, SQLUserJobRepository
from .infrastructure.scrapers.remote_ok import RemoteOkScraper
from .infrastructure.matchers.gemini import GeminiMatcher
from .infrastructure.telegram.bot import send_job_alert
from .application.use_cases import SearchAndMatchJobsUseCase

logger = logging.getLogger(__name__)

async def run_search_loop(bot=None, target_user_id: int = None):
    db = SessionLocal()
    try:
        user_repo = SQLUserRepository(db)
        job_repo = SQLJobRepository(db)
        user_job_repo = SQLUserJobRepository(db)
        scraper = RemoteOkScraper()
        matcher = GeminiMatcher()

        use_case = SearchAndMatchJobsUseCase(user_repo, job_repo, user_job_repo, scraper, matcher)

        async def on_match_found(telegram_id, user_job):
            if bot:
                await send_job_alert(bot, telegram_id, user_job)

        await use_case.execute(target_telegram_id=target_user_id, on_match_found=on_match_found)
    finally:
        db.close()
