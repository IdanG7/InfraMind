"""Integration tests for complete workflows"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.models.orm import Base, Run, Step, Feature, Pipeline
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
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_complete_workflow(client, db_session):
    """Test complete run ingestion -> feature extraction -> optimization workflow"""

    # Step 1: Ingest a run
    headers = {"X-IM-Token": "dev-key-change-in-production"}

    run_payload = {
        "pipeline": "integration-test/pipeline",
        "build_number": 1,
        "git_sha": "abc123def456",
        "git_branch": "main",
        "start_time": "2025-01-01T10:00:00Z",
        "end_time": "2025-01-01T10:10:00Z",
        "duration_s": 600.0,
        "status": "success",
        "tool": "pytest",
        "concurrency": 4,
        "cpu_req": 4,
        "mem_req_gb": 8,
        "steps": [
            {
                "name": "checkout",
                "start_time": "2025-01-01T10:00:00Z",
                "end_time": "2025-01-01T10:01:00Z",
                "duration_s": 60.0,
                "cpu_usage_pct": 50.0,
                "rss_max_bytes": 1073741824,  # 1GB
                "io_r_bytes": 10485760,  # 10MB
                "io_w_bytes": 5242880,  # 5MB
                "exit_code": 0,
            },
            {
                "name": "build",
                "start_time": "2025-01-01T10:01:00Z",
                "end_time": "2025-01-01T10:09:00Z",
                "duration_s": 480.0,
                "cpu_usage_pct": 350.0,
                "rss_max_bytes": 8589934592,  # 8GB
                "io_r_bytes": 104857600,  # 100MB
                "io_w_bytes": 52428800,  # 50MB
                "exit_code": 0,
            },
            {
                "name": "test",
                "start_time": "2025-01-01T10:09:00Z",
                "end_time": "2025-01-01T10:10:00Z",
                "duration_s": 60.0,
                "cpu_usage_pct": 200.0,
                "rss_max_bytes": 2147483648,  # 2GB
                "io_r_bytes": 20971520,  # 20MB
                "io_w_bytes": 10485760,  # 10MB
                "exit_code": 0,
            },
        ],
    }

    response = client.post("/runs", json=run_payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "ingested"
    run_id = data["run_id"]

    # Step 2: Verify run was stored
    run = db_session.query(Run).filter(Run.id == run_id).first()
    assert run is not None
    assert run.pipeline.name == "integration-test/pipeline"
    assert run.build_number == 1
    assert run.status == "success"
    assert len(run.steps) == 3

    # Step 3: Verify steps were stored
    steps = db_session.query(Step).filter(Step.run_id == run_id).all()
    assert len(steps) == 3
    assert steps[0].name == "checkout"
    assert steps[1].name == "build"
    assert steps[2].name == "test"

    # Step 4: Verify features were extracted
    features = db_session.query(Feature).filter(Feature.run_id == run_id).first()
    assert features is not None
    assert features.tool == "pytest"
    assert features.max_rss_gb > 0
    assert features.num_steps == 3

    # Step 5: Get optimization suggestions
    optimize_payload = {
        "pipeline": "integration-test/pipeline",
        "context": {
            "tool": "pytest",
            "max_rss_gb": 8.0,
            "num_steps": 3,
            "avg_step_duration_s": 200,
        },
    }

    response = client.post("/optimize", json=optimize_payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "suggestions" in data
    assert "rationale" in data
    assert "confidence" in data

    suggestions = data["suggestions"]
    assert suggestions["concurrency"] >= 1
    assert suggestions["cpu_req"] >= 1
    assert suggestions["mem_req_gb"] >= 2
    assert "cache" in suggestions


def test_multiple_runs_same_pipeline(client, db_session):
    """Test ingesting multiple runs for the same pipeline"""

    headers = {"X-IM-Token": "dev-key-change-in-production"}

    # Ingest 3 runs for the same pipeline
    for build_num in range(1, 4):
        run_payload = {
            "pipeline": "multi-run/pipeline",
            "build_number": build_num,
            "git_sha": f"sha{build_num}",
            "git_branch": "main",
            "start_time": "2025-01-01T10:00:00Z",
            "end_time": "2025-01-01T10:05:00Z",
            "duration_s": 300.0,
            "status": "success",
            "tool": "npm",
            "concurrency": 2,
            "cpu_req": 2,
            "mem_req_gb": 4,
            "steps": [
                {
                    "name": "test",
                    "start_time": "2025-01-01T10:00:00Z",
                    "end_time": "2025-01-01T10:05:00Z",
                    "duration_s": 300.0,
                    "cpu_usage_pct": 150.0,
                    "rss_max_bytes": 4294967296,  # 4GB
                    "io_r_bytes": 10485760,
                    "io_w_bytes": 5242880,
                    "exit_code": 0,
                }
            ],
        }

        response = client.post("/runs", json=run_payload, headers=headers)
        assert response.status_code == 201

    # Verify all runs were stored
    pipeline = db_session.query(Pipeline).filter(Pipeline.name == "multi-run/pipeline").first()
    runs = db_session.query(Run).filter(Run.pipeline_id == pipeline.id).all()
    assert len(runs) == 3

    # Verify features for all runs
    features = (
        db_session.query(Feature)
        .join(Run)
        .filter(Run.pipeline == "multi-run/pipeline")
        .all()
    )
    assert len(features) == 3


def test_failed_run_ingestion(client, db_session):
    """Test ingesting a failed run"""

    headers = {"X-IM-Token": "dev-key-change-in-production"}

    run_payload = {
        "pipeline": "failed-run/pipeline",
        "build_number": 1,
        "git_sha": "fail123",
        "git_branch": "bugfix",
        "start_time": "2025-01-01T10:00:00Z",
        "end_time": "2025-01-01T10:02:00Z",
        "duration_s": 120.0,
        "status": "failed",
        "tool": "gradle",
        "concurrency": 4,
        "cpu_req": 4,
        "mem_req_gb": 8,
        "steps": [
            {
                "name": "compile",
                "start_time": "2025-01-01T10:00:00Z",
                "end_time": "2025-01-01T10:02:00Z",
                "duration_s": 120.0,
                "cpu_usage_pct": 100.0,
                "rss_max_bytes": 2147483648,  # 2GB
                "io_r_bytes": 10485760,
                "io_w_bytes": 5242880,
                "exit_code": 1,
            }
        ],
    }

    response = client.post("/runs", json=run_payload, headers=headers)
    assert response.status_code == 201

    # Verify failed run was stored
    pipeline = db_session.query(Pipeline).filter(Pipeline.name == "failed-run/pipeline").first()
    run = db_session.query(Run).filter(Run.pipeline_id == pipeline.id).first()
    assert run is not None
    assert run.status == "failed"
    assert run.steps[0].exit_code == 1


def test_authentication_required(client):
    """Test that authentication is required for protected endpoints"""

    # Minimal valid payload for runs endpoint
    run_payload = {
        "pipeline": "test/pipeline",
        "build_number": 1,
        "git_sha": "abc123",
        "git_branch": "main",
        "start_time": "2025-01-01T10:00:00Z",
        "end_time": "2025-01-01T10:05:00Z",
        "duration_s": 300.0,
        "status": "success",
        "tool": "test",
        "concurrency": 1,
        "cpu_req": 1,
        "mem_req_gb": 2,
        "steps": [],
    }

    # No auth header
    response = client.post("/runs", json=run_payload)
    assert response.status_code == 403

    # Wrong API key
    headers = {"X-IM-Token": "wrong-key"}
    response = client.post("/runs", json=run_payload, headers=headers)
    assert response.status_code == 403

    # Optimization endpoint
    optimize_payload = {
        "pipeline": "test/pipeline",
        "context": {"tool": "cmake"},
    }
    response = client.post("/optimize", json=optimize_payload)
    assert response.status_code == 403


def test_healthz_with_database(client, db_session):
    """Test health endpoint returns database status"""

    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "database" in data
    assert data["database"] in ["connected", "ok"]


def test_optimization_with_constraints(client):
    """Test optimization respects constraints"""

    headers = {"X-IM-Token": "dev-key-change-in-production"}

    payload = {
        "pipeline": "constrained/pipeline",
        "context": {
            "tool": "maven",
            "max_rss_gb": 16.0,
        },
        "constraints": {
            "max_concurrency": 2,
            "min_ram_gb": 32,
        },
    }

    response = client.post("/optimize", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()

    suggestions = data["suggestions"]
    assert suggestions["concurrency"] <= 2
    assert suggestions["mem_req_gb"] >= 32
