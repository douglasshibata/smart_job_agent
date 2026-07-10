from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from .entities import User, Job, UserJob

class UserRepository(ABC):
    @abstractmethod
    def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        pass

    @abstractmethod
    def save(self, user: User) -> User:
        pass

    @abstractmethod
    def get_all(self) -> List[User]:
        pass

class JobRepository(ABC):
    @abstractmethod
    def get_by_external_id(self, external_id: str) -> Optional[Job]:
        pass

    @abstractmethod
    def save(self, job: Job) -> Job:
        pass

class UserJobRepository(ABC):
    @abstractmethod
    def get_by_user_and_job(self, user_id: int, job_id: int) -> Optional[UserJob]:
        pass

    @abstractmethod
    def save(self, user_job: UserJob) -> UserJob:
        pass

    @abstractmethod
    def get_by_id(self, user_job_id: int) -> Optional[UserJob]:
        pass

class JobScraper(ABC):
    @abstractmethod
    async def get_all_jobs(self) -> List[Dict[str, Any]]:
        pass

class JobMatcher(ABC):
    @abstractmethod
    async def score_job(self, user: User, job: Job) -> Dict[str, Any]:
        pass

class JobApplier(ABC):
    @abstractmethod
    async def apply_to_job(self, user: User, user_job: UserJob) -> bool:
        pass
