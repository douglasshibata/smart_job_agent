from sqlalchemy import Column, Integer, BigInteger, String, Boolean, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import datetime
from .connection import Base

class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True)
    username = Column(String)
    resume_text = Column(Text, nullable=True)

    # Preferences
    keywords = Column(String, nullable=True) # Comma separated
    location = Column(String, nullable=True)
    salary_min = Column(Integer, nullable=True)
    remote_only = Column(Boolean, default=False)

    actions = relationship("UserJobModel", back_populates="user")


class JobModel(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True)
    title = Column(String)
    company = Column(String)
    location = Column(String)
    salary = Column(String, nullable=True)
    link = Column(String)
    description = Column(Text)
    posted_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    user_actions = relationship("UserJobModel", back_populates="job")


class UserJobModel(Base):
    __tablename__ = "user_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    job_id = Column(Integer, ForeignKey("jobs.id"))
    status = Column(String, default="new")
    relevance_score = Column(Float, nullable=True)
    matching_reason = Column(Text, nullable=True)
    cover_letter_draft = Column(Text, nullable=True)

    user = relationship("UserModel", back_populates="actions")
    job = relationship("JobModel", back_populates="user_actions")
