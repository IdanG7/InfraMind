"""Dependency injection"""

from typing import Generator

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from .config import settings
from .storage.postgres import SessionLocal

# Security
api_key_header = APIKeyHeader(name="X-IM-Token", auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """Verify API key"""
    if api_key != settings.api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key
