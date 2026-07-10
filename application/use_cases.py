import logging
from typing import Optional, Dict, Any, Callable, Coroutine
from ..domain.entities import User, Job, UserJob
from ..domain.interfaces import UserRepository, JobRepository, UserJobRepository, JobScraper, JobMatcher, JobApplier

logger = logging.getLogger(__name__)

class RegisterOrGetUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def execute(self, telegram_id: int, username: Optional[str]) -> User:
        user = self.user_repo.get_by_telegram_id(telegram_id)
        if not user:
            user = User(telegram_id=telegram_id, username=username)
            user = self.user_repo.save(user)
        return user


class UpdateResumeUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def execute(self, telegram_id: int, resume_text: str) -> bool:
        user = self.user_repo.get_by_telegram_id(telegram_id)
        if user:
            user.resume_text = resume_text
            self.user_repo.save(user)
            return True
        return False


class UpdatePreferencesUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def execute(self, telegram_id: int, preferences_data: Dict[str, Any]) -> bool:
        user = self.user_repo.get_by_telegram_id(telegram_id)
        if user:
            if "keywords" in preferences_data:
                user.keywords = preferences_data["keywords"]
            if "location" in preferences_data:
                user.location = preferences_data["location"]
            if "salary_min" in preferences_data:
                user.salary_min = preferences_data["salary_min"]
            if "remote_only" in preferences_data:
                user.remote_only = preferences_data["remote_only"]
            self.user_repo.save(user)
            return True
        return False


class SearchAndMatchJobsUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        job_repo: JobRepository,
        user_job_repo: UserJobRepository,
        scraper: JobScraper,
        matcher: JobMatcher
    ):
        self.user_repo = user_repo
        self.job_repo = job_repo
        self.user_job_repo = user_job_repo
        self.scraper = scraper
        self.matcher = matcher

    async def execute(
        self,
        target_telegram_id: Optional[int] = None,
        on_match_found: Optional[Callable[[int, UserJob], Coroutine[Any, Any, None]]] = None
    ) -> None:
        logger.info(f"Starting job search use case (target: {target_telegram_id or 'ALL'})...")
        if target_telegram_id:
            user = self.user_repo.get_by_telegram_id(target_telegram_id)
            users = [user] if user else []
        else:
            users = self.user_repo.get_all()

        if not users:
            logger.info("No users found to match. Skipping search.")
            return

        new_jobs_data = await self.scraper.get_all_jobs()
        logger.info(f"Scraped {len(new_jobs_data)} jobs in total.")

        for job_data in new_jobs_data:
            job = self.job_repo.get_by_external_id(job_data["external_id"])
            if not job:
                job = Job(
                    external_id=job_data["external_id"],
                    title=job_data["title"],
                    company=job_data["company"],
                    location=job_data["location"],
                    salary=job_data["salary"],
                    link=job_data["link"],
                    description=job_data["description"]
                )
                job = self.job_repo.save(job)

            for user in users:
                # Basic keyword pre-filtering to save LLM tokens
                if user.keywords:
                    keywords = [k.strip().lower() for k in user.keywords.split(',')]
                    title_desc = (job.title + " " + (job.description or "")).lower()
                    if not any(k in title_desc for k in keywords):
                        continue

                existing_action = self.user_job_repo.get_by_user_and_job(user.id, job.id)
                if not existing_action:
                    logger.info(f"Matching job {job.id} for user {user.username}")
                    match_result = await self.matcher.score_job(user, job)

                    user_job = UserJob(
                        user_id=user.id,
                        job_id=job.id,
                        status="new",
                        relevance_score=match_result["relevance_score"],
                        matching_reason=match_result["reason"],
                        cover_letter_draft=match_result["cover_letter"]
                    )
                    user_job = self.user_job_repo.save(user_job)
                    user_job.user = user
                    user_job.job = job

                    if user_job.relevance_score >= 70 and on_match_found:
                        try:
                            await on_match_found(user.telegram_id, user_job)
                        except Exception as e:
                            logger.error(f"Error executing on_match_found trigger for {user.telegram_id}: {e}")

        logger.info("Job search use case completed.")


class ApplyToJobUseCase:
    def __init__(
        self,
        user_job_repo: UserJobRepository,
        applier: JobApplier
    ):
        self.user_job_repo = user_job_repo
        self.applier = applier

    async def execute(self, user_job_id: int) -> tuple[bool, Optional[UserJob]]:
        user_job = self.user_job_repo.get_by_id(user_job_id)
        if not user_job:
            logger.error(f"UserJob with ID {user_job_id} not found.")
            return False, None

        success = await self.applier.apply_to_job(user_job.user, user_job)
        if success:
            user_job.status = "applied"
            self.user_job_repo.save(user_job)
        return success, user_job


class IgnoreJobUseCase:
    def __init__(self, user_job_repo: UserJobRepository):
        self.user_job_repo = user_job_repo

    def execute(self, user_job_id: int) -> tuple[bool, Optional[UserJob]]:
        user_job = self.user_job_repo.get_by_id(user_job_id)
        if not user_job:
            return False, None
        user_job.status = "ignored"
        self.user_job_repo.save(user_job)
        return True, user_job


class SaveJobUseCase:
    def __init__(self, user_job_repo: UserJobRepository):
        self.user_job_repo = user_job_repo

    def execute(self, user_job_id: int) -> tuple[bool, Optional[UserJob]]:
        user_job = self.user_job_repo.get_by_id(user_job_id)
        if not user_job:
            return False, None
        user_job.status = "saved"
        self.user_job_repo.save(user_job)
        return True, user_job
