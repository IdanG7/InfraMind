"""Tests for API endpoints"""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.models.orm import Base
from app.deps import get_db
import os

# Test database URL
TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test.db")

# Create test engine
engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False} if "sqlite" in TEST_DB_URL else {},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def test_db():
    """Create test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_db):
    """Get database session"""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Get test client with overridden database"""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_healthz(client):
    """Test health endpoint"""
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_root(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "InfraMind API"


def test_optimize_requires_auth(client):
    """Test /optimize requires authentication"""
    payload = {
        "pipeline": "test/pipeline",
        "context": {"tool": "cmake"},
    }
    response = client.post("/optimize", json=payload)
    assert response.status_code == 403


def test_optimize_with_auth(client):
    """Test /optimize with authentication"""
    headers = {"X-IM-Token": "dev-key-change-in-production"}

    payload = {
        "pipeline": "test/pipeline",
        "context": {
            "tool": "cmake",
            "max_rss_gb": 4.0,
            "num_steps": 5,
            "avg_step_duration_s": 60,
        },
    }

    response = client.post("/optimize", json=payload, headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert "suggestions" in data
    assert "rationale" in data
    assert "confidence" in data

    suggestions = data["suggestions"]
    assert "concurrency" in suggestions
    assert "cpu_req" in suggestions
    assert "mem_req_gb" in suggestions
