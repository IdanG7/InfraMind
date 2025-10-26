"""Health check endpoints"""

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..config import settings
from ..deps import get_db
from ..models.schemas import HealthResp
from ..storage.redis import redis_client

router = APIRouter()


@router.get("/healthz", response_model=HealthResp)
async def healthz(db: Session = Depends(get_db)) -> HealthResp:
    """Health check - liveness probe"""
    # Check database
    db_status = "connected"
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    return HealthResp(
        status="ok",
        version=settings.api_version,
        timestamp=datetime.utcnow(),
        database=db_status,
    )


@router.get("/readyz", response_model=HealthResp)
async def readyz(db: Session = Depends(get_db)) -> HealthResp:
    """Readiness check - includes dependencies"""
    # Check database
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
    except Exception as e:
        return HealthResp(
            status=f"error: database unavailable - {e}",
            version=settings.api_version,
            timestamp=datetime.utcnow(),
        )

    # Check Redis
    try:
        redis_client.ping()
    except Exception as e:
        return HealthResp(
            status=f"error: redis unavailable - {e}",
            version=settings.api_version,
            timestamp=datetime.utcnow(),
        )

    return HealthResp(
        status="ready",
        version=settings.api_version,
        timestamp=datetime.utcnow(),
    )
