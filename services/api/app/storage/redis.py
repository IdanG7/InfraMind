"""Redis cache storage"""

import json
from typing import Any

import redis

from ..config import settings

redis_client = redis.from_url(settings.redis_url, decode_responses=True)


def cache_features(run_id: str, features: dict[str, Any], ttl: int | None = None) -> None:
    """Cache feature vector"""
    key = f"im:feat:{run_id}"
    ttl = ttl or settings.feature_cache_ttl
    redis_client.setex(key, ttl, json.dumps(features))


def get_cached_features(run_id: str) -> dict[str, Any] | None:
    """Get cached features"""
    key = f"im:feat:{run_id}"
    data = redis_client.get(key)
    return json.loads(data) if data else None


def cache_suggestion(pipeline: str, suggestion: dict[str, Any]) -> None:
    """Cache last suggestion for pipeline"""
    key = f"im:last_suggest:{pipeline}"
    redis_client.set(key, json.dumps(suggestion))


def get_cached_suggestion(pipeline: str) -> dict[str, Any] | None:
    """Get cached suggestion"""
    key = f"im:last_suggest:{pipeline}"
    data = redis_client.get(key)
    return json.loads(data) if data else None


def get_active_model_version() -> str:
    """Get active model version"""
    version = redis_client.get("im:model:active")
    return version or "v1"


def set_active_model_version(version: str) -> None:
    """Set active model version"""
    redis_client.set("im:model:active", version)
