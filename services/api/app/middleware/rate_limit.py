"""Rate limiting middleware using slowapi"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request

from ..config import settings


def get_api_key_or_ip(request: Request) -> str:
    """
    Rate limit by API key if present, otherwise by IP address.
    This allows authenticated users to have separate rate limits.
    """
    api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization")
    if api_key:
        return f"key:{api_key[:16]}"  # Use first 16 chars of key
    return get_remote_address(request)


# Create limiter instance
limiter = Limiter(
    key_func=get_api_key_or_ip,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"],
    enabled=settings.rate_limit_enabled,
    storage_uri=settings.redis_url,  # Use Redis for distributed rate limiting
)


def setup_rate_limiting(app):
    """Configure rate limiting for the app"""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    return limiter
