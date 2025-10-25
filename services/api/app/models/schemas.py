"""Pydantic schemas for API requests/responses"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class BuildStartReq(BaseModel):
    """Build start request"""

    pipeline: str
    run_id: str
    git: str | None = None
    branch: str
    commit: str
    image: str
    tools: list[str] = Field(default_factory=list)
    k8s_node: str | None = None
    requested_resources: dict[str, Any] = Field(default_factory=dict)


class BuildStepReq(BaseModel):
    """Build step event request"""

    run_id: str
    stage: str
    step: str
    span_id: str
    event: str  # "start" or "stop"
    timestamp: datetime
    counters: dict[str, Any] = Field(default_factory=dict)


class BuildCompleteReq(BaseModel):
    """Build completion request"""

    run_id: str
    status: str  # "success", "failure", "aborted"
    duration_s: float
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    cache: dict[str, Any] = Field(default_factory=dict)


class OptimizeReq(BaseModel):
    """Optimization request"""

    pipeline: str
    run_id: str | None = None
    context: dict[str, Any]
    constraints: dict[str, Any] | None = None


class OptimizeResp(BaseModel):
    """Optimization response"""

    suggestions: dict[str, Any]
    rationale: str
    confidence: float


class FeatureResp(BaseModel):
    """Feature vector response"""

    run_id: str
    vector: dict[str, Any]
    label: dict[str, Any] | None = None
    created_at: datetime


class HealthResp(BaseModel):
    """Health check response"""

    status: str
    version: str
    timestamp: datetime
