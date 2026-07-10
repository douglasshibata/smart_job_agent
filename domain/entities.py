from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional

class JobStatus(str, Enum):
    NEW = "new"
    SEEN = "seen"
    APPLIED = "applied"
    IGNORED = "ignored"
    SAVED = "saved"

@dataclass
class User:
    id: Optional[int] = None
    telegram_id: Optional[int] = None
    username: Optional[str] = None
    resume_text: Optional[str] = None
    keywords: Optional[str] = None
    location: Optional[str] = None
    salary_min: Optional[int] = None
    remote_only: bool = False
    actions: List["UserJob"] = field(default_factory=list)

@dataclass
class Job:
    id: Optional[int] = None
    external_id: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[str] = None
    link: Optional[str] = None
    description: Optional[str] = None
    posted_at: Optional[datetime] = None

@dataclass
class UserJob:
    id: Optional[int] = None
    user_id: Optional[int] = None
    job_id: Optional[int] = None
    status: str = JobStatus.NEW.value
    relevance_score: Optional[float] = None
    matching_reason: Optional[str] = None
    cover_letter_draft: Optional[str] = None
    user: Optional[User] = None
    job: Optional[Job] = None
