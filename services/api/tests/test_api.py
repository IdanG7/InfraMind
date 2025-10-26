"""Tests for API endpoints"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_healthz():
    """Test health endpoint"""
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "InfraMind API"


def test_optimize_requires_auth():
    """Test /optimize requires authentication"""
    payload = {
        "pipeline": "test/pipeline",
        "context": {"tool": "cmake"},
    }
    response = client.post("/optimize", json=payload)
    assert response.status_code == 403


def test_optimize_with_auth():
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
