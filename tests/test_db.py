import pytest
from smart_job_agent.database import engine, Base, SessionLocal
from smart_job_agent.models import User, Job, UserJob

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_user_creation(db):
    user = User(telegram_id=12345, username="testuser")
    db.add(user)
    db.commit()

    saved_user = db.query(User).filter(User.telegram_id == 12345).first()
    assert saved_user.username == "testuser"

def test_job_link_to_user(db):
    user = User(telegram_id=123, username="u")
    job = Job(external_id="j1", title="T", company="C", link="L", description="D")
    db.add(user)
    db.add(job)
    db.commit()

    user_job = UserJob(user_id=user.id, job_id=job.id, relevance_score=90.0)
    db.add(user_job)
    db.commit()

    assert len(user.actions) == 1
    assert user.actions[0].relevance_score == 90.0
