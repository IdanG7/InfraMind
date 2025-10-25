"""Feature endpoints"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..deps import get_db
from ..models.orm import Feature
from ..models.schemas import FeatureResp
from ..storage.redis import get_cached_features

router = APIRouter()


@router.get("/{run_id}", response_model=FeatureResp)
async def get_features(run_id: str, db: Session = Depends(get_db)) -> FeatureResp:
    """Get feature vector for a run"""
    # Try cache first
    cached = get_cached_features(run_id)
    if cached:
        return FeatureResp(
            run_id=run_id,
            vector=cached["vector"],
            label=cached.get("label"),
            created_at=cached["created_at"],
        )

    # Query database
    feature = db.query(Feature).filter(Feature.run_id == run_id).first()
    if not feature:
        raise HTTPException(status_code=404, detail="Features not found")

    return FeatureResp(
        run_id=feature.run_id,
        vector=feature.vector,
        label=feature.label,
        created_at=feature.created_at,
    )
