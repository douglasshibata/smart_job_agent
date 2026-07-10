from typing import List, Optional
from sqlalchemy.orm import Session
from ...domain.entities import User, Job, UserJob
from ...domain.interfaces import UserRepository, JobRepository, UserJobRepository
from .models import UserModel, JobModel, UserJobModel

class SQLUserRepository(UserRepository):
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def _to_entity(self, model: UserModel) -> Optional[User]:
        if not model:
            return None
        return User(
            id=model.id,
            telegram_id=model.telegram_id,
            username=model.username,
            resume_text=model.resume_text,
            keywords=model.keywords,
            location=model.location,
            salary_min=model.salary_min,
            remote_only=model.remote_only
        )

    def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        model = self.db_session.query(UserModel).filter(UserModel.telegram_id == telegram_id).first()
        return self._to_entity(model)

    def get_all(self) -> List[User]:
        models = self.db_session.query(UserModel).all()
        return [self._to_entity(m) for m in models]

    def save(self, user: User) -> User:
        if user.id:
            model = self.db_session.query(UserModel).filter(UserModel.id == user.id).first()
        else:
            model = self.db_session.query(UserModel).filter(UserModel.telegram_id == user.telegram_id).first()

        if not model:
            model = UserModel(
                telegram_id=user.telegram_id,
                username=user.username,
                resume_text=user.resume_text,
                keywords=user.keywords,
                location=user.location,
                salary_min=user.salary_min,
                remote_only=user.remote_only
            )
            self.db_session.add(model)
        else:
            model.username = user.username
            model.resume_text = user.resume_text
            model.keywords = user.keywords
            model.location = user.location
            model.salary_min = user.salary_min
            model.remote_only = user.remote_only

        self.db_session.commit()
        self.db_session.refresh(model)
        user.id = model.id
        return user


class SQLJobRepository(JobRepository):
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def _to_entity(self, model: JobModel) -> Optional[Job]:
        if not model:
            return None
        return Job(
            id=model.id,
            external_id=model.external_id,
            title=model.title,
            company=model.company,
            location=model.location,
            salary=model.salary,
            link=model.link,
            description=model.description,
            posted_at=model.posted_at
        )

    def get_by_external_id(self, external_id: str) -> Optional[Job]:
        model = self.db_session.query(JobModel).filter(JobModel.external_id == external_id).first()
        return self._to_entity(model)

    def save(self, job: Job) -> Job:
        if job.id:
            model = self.db_session.query(JobModel).filter(JobModel.id == job.id).first()
        else:
            model = self.db_session.query(JobModel).filter(JobModel.external_id == job.external_id).first()

        if not model:
            model = JobModel(
                external_id=job.external_id,
                title=job.title,
                company=job.company,
                location=job.location,
                salary=job.salary,
                link=job.link,
                description=job.description,
                posted_at=job.posted_at
            )
            self.db_session.add(model)
        else:
            model.title = job.title
            model.company = job.company
            model.location = job.location
            model.salary = job.salary
            model.link = job.link
            model.description = job.description
            if job.posted_at:
                model.posted_at = job.posted_at

        self.db_session.commit()
        self.db_session.refresh(model)
        job.id = model.id
        return job


class SQLUserJobRepository(UserJobRepository):
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def _to_entity(self, model: UserJobModel) -> Optional[UserJob]:
        if not model:
            return None

        user_entity = None
        if model.user:
            user_entity = User(
                id=model.user.id,
                telegram_id=model.user.telegram_id,
                username=model.user.username,
                resume_text=model.user.resume_text,
                keywords=model.user.keywords,
                location=model.user.location,
                salary_min=model.user.salary_min,
                remote_only=model.user.remote_only
            )

        job_entity = None
        if model.job:
            job_entity = Job(
                id=model.job.id,
                external_id=model.job.external_id,
                title=model.job.title,
                company=model.job.company,
                location=model.job.location,
                salary=model.job.salary,
                link=model.job.link,
                description=model.job.description,
                posted_at=model.job.posted_at
            )

        return UserJob(
            id=model.id,
            user_id=model.user_id,
            job_id=model.job_id,
            status=model.status,
            relevance_score=model.relevance_score,
            matching_reason=model.matching_reason,
            cover_letter_draft=model.cover_letter_draft,
            user=user_entity,
            job=job_entity
        )

    def get_by_user_and_job(self, user_id: int, job_id: int) -> Optional[UserJob]:
        model = self.db_session.query(UserJobModel).filter(
            UserJobModel.user_id == user_id,
            UserJobModel.job_id == job_id
        ).first()
        return self._to_entity(model)

    def get_by_id(self, user_job_id: int) -> Optional[UserJob]:
        model = self.db_session.query(UserJobModel).filter(UserJobModel.id == user_job_id).first()
        return self._to_entity(model)

    def save(self, user_job: UserJob) -> UserJob:
        if user_job.id:
            model = self.db_session.query(UserJobModel).filter(UserJobModel.id == user_job.id).first()
        else:
            model = self.db_session.query(UserJobModel).filter(
                UserJobModel.user_id == user_job.user_id,
                UserJobModel.job_id == user_job.job_id
            ).first()

        if not model:
            model = UserJobModel(
                user_id=user_job.user_id,
                job_id=user_job.job_id,
                status=user_job.status,
                relevance_score=user_job.relevance_score,
                matching_reason=user_job.matching_reason,
                cover_letter_draft=user_job.cover_letter_draft
            )
            self.db_session.add(model)
        else:
            model.status = user_job.status
            model.relevance_score = user_job.relevance_score
            model.matching_reason = user_job.matching_reason
            model.cover_letter_draft = user_job.cover_letter_draft

        self.db_session.commit()
        self.db_session.refresh(model)
        user_job.id = model.id
        return user_job
