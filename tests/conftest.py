"""Shared test fixtures: in-memory SQLite DB, TestClient, auth helpers."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from job_coach.app.core.security import create_access_token
from job_coach.app.db.base import Base
from job_coach.app.db.dependencies import get_db
from job_coach.app.main import app

# In-memory SQLite for fast isolated tests
TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    """Create all tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    """Provide a clean DB session for direct service-layer tests."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client():
    """FastAPI TestClient with DB dependency overridden."""

    def _override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def registered_user(client: TestClient) -> dict:
    """Register a user and return the response data."""
    resp = client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "strongpass123",
        },
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture()
def auth_headers(registered_user: dict) -> dict:
    """Return Authorization headers with a valid JWT for the test user."""
    token = create_access_token(data={"sub": str(registered_user["id"])})
    return {"Authorization": f"Bearer {token}"}
