import pytest
from smart_job_agent.infrastructure.database.connection import engine, Base, SessionLocal
from smart_job_agent.infrastructure.database.repositories import SQLUserRepository, SQLJobRepository, SQLUserJobRepository
from smart_job_agent.domain.entities import User, Job, UserJob

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_user_creation(db):
    user_repo = SQLUserRepository(db)
    user = User(telegram_id=12345, username="testuser")
    user_repo.save(user)

    saved_user = user_repo.get_by_telegram_id(12345)
    assert saved_user is not None
    assert saved_user.username == "testuser"

def test_job_link_to_user(db):
    user_repo = SQLUserRepository(db)
    job_repo = SQLJobRepository(db)
    user_job_repo = SQLUserJobRepository(db)

    user = User(telegram_id=123, username="u")
    user_repo.save(user)

    job = Job(external_id="j1", title="T", company="C", link="L", description="D")
    job_repo.save(job)

    user_job = UserJob(user_id=user.id, job_id=job.id, relevance_score=90.0)
    user_job_repo.save(user_job)

    # Let's retrieve by user and job
    saved_user_job = user_job_repo.get_by_user_and_job(user.id, job.id)
    assert saved_user_job is not None
    assert saved_user_job.relevance_score == 90.0
    assert saved_user_job.user.username == "u"
    assert saved_user_job.job.title == "T"
