"""Tests for ML optimizer"""

import pytest
from app.ml.optimizer import suggest, clamp, candidate_configs


def test_clamp():
    """Test value clamping"""
    assert clamp(5, 1, 10) == 5
    assert clamp(0, 1, 10) == 1
    assert clamp(15, 1, 10) == 10


def test_candidate_configs():
    """Test candidate generation"""
    context = {
        "last_success": {
            "concurrency": 4,
            "cpu_req": 4,
            "mem_req_gb": 8,
        }
    }

    candidates = candidate_configs(context)

    assert len(candidates) > 0
    assert len(candidates) <= 20  # Limited to 20

    # Check bounds
    for cfg in candidates:
        assert 1 <= cfg["concurrency"] <= 16
        assert 1 <= cfg["cpu_req"] <= 16
        assert 2 <= cfg["mem_req_gb"] <= 64


def test_suggest_basic():
    """Test basic optimization"""
    context = {
        "tool": "cmake",
        "max_rss_gb": 4.0,
        "num_steps": 5,
        "avg_step_duration_s": 60,
    }

    constraints = {}

    suggestions, rationale, confidence = suggest(context, constraints)

    assert "concurrency" in suggestions
    assert "cpu_req" in suggestions
    assert "mem_req_gb" in suggestions
    assert "cache" in suggestions

    assert 1 <= suggestions["concurrency"] <= 16
    assert 1 <= suggestions["cpu_req"] <= 16
    assert 2 <= suggestions["mem_req_gb"] <= 64

    assert isinstance(rationale, str)
    assert len(rationale) > 0
    assert 0 <= confidence <= 1


def test_suggest_with_constraints():
    """Test optimization with constraints"""
    context = {
        "tool": "cmake",
        "max_rss_gb": 4.0,
    }

    constraints = {
        "max_concurrency": 4,
        "min_ram_gb": 16,
    }

    suggestions, _, _ = suggest(context, constraints)

    assert suggestions["concurrency"] <= 4
    assert suggestions["mem_req_gb"] >= 16


def test_safety_guards():
    """Test safety guard application"""
    from app.ml.optimizer import apply_safety_guards

    config = {"concurrency": 8, "cpu_req": 1, "mem_req_gb": 2}

    context = {"max_rss_bytes": 10 * 1024**3}  # 10 GB RSS

    safe = apply_safety_guards(config, context)

    # Memory should be >= 10GB * 1.2 = 12GB
    assert safe["mem_req_gb"] >= 12

    # CPU should be >= concurrency / 4 = 2
    assert safe["cpu_req"] >= 2
