import logging
from .database import SessionLocal
from .models import User, Job, UserJob
from .scraper import Scraper
from .matcher import Matcher
from .bot import send_job_alert

logger = logging.getLogger(__name__)

scraper = Scraper()
matcher = Matcher()

async def run_search_loop(bot=None, target_user_id: int = None):
    logger.info(f"Starting job search loop (target: {target_user_id or 'ALL'})...")
    db = SessionLocal()
    if target_user_id:
        users = db.query(User).filter(User.telegram_id == target_user_id).all()
    else:
        users = db.query(User).all()

    if not users:
        logger.info("No users found in database. Skipping search.")
        db.close()
        return

    new_jobs_data = await scraper.get_all_jobs()
    logger.info(f"Found {len(new_jobs_data)} jobs in total from scrapers.")

    for job_data in new_jobs_data:
        # 1. Save or get the job
        job = db.query(Job).filter(Job.external_id == job_data["external_id"]).first()
        if not job:
            job = Job(**job_data)
            db.add(job)
            db.commit()
            db.refresh(job)

        # 2. Match with each user
        for user in users:
            # Basic keyword pre-filtering to save tokens
            if user.keywords:
                keywords = [k.strip().lower() for k in user.keywords.split(',')]
                title_desc = (job.title + " " + (job.description or "")).lower()
                if not any(k in title_desc for k in keywords):
                    continue

            # Check if already processed for this user
            existing_action = db.query(UserJob).filter(
                UserJob.user_id == user.id,
                UserJob.job_id == job.id
            ).first()

            if not existing_action:
                logger.info(f"Matching job {job.id} for user {user.username}")
                match_result = await matcher.score_job(user, job)

                user_job = UserJob(
                    user_id=user.id,
                    job_id=job.id,
                    relevance_score=match_result["relevance_score"],
                    matching_reason=match_result["reason"],
                    cover_letter_draft=match_result["cover_letter"]
                )
                db.add(user_job)
                db.commit()
                db.refresh(user_job)

                # 3. Alert if score is high enough (e.g., > 70) and bot is provided
                if user_job.relevance_score >= 70 and bot:
                    try:
                        await send_job_alert(bot, user.telegram_id, user_job)
                    except Exception as e:
                        logger.error(f"Failed to send alert to {user.telegram_id}: {e}")

    db.close()
    logger.info("Job search loop completed.")
