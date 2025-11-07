"""Optimization endpoint"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..deps import get_db, verify_api_key
from ..ml.optimizer import suggest
from ..models.schemas import OptimizeReq, OptimizeResp
from ..models.orm import Suggestion, Pipeline
from ..storage.redis import cache_suggestion

router = APIRouter()


@router.post("/optimize", response_model=OptimizeResp, dependencies=[Depends(verify_api_key)])
async def optimize(req: OptimizeReq, db: Session = Depends(get_db)) -> OptimizeResp:
    """Get optimization suggestions"""
    # Call ML optimizer
    suggestions, rationale, confidence = suggest(req.context, req.constraints or {})

    # Cache suggestion
    cache_suggestion(req.pipeline, suggestions)

    # Store in database
    pipeline = db.query(Pipeline).filter(Pipeline.name == req.pipeline).first()
    if pipeline:
        suggestion_record = Suggestion(
            pipeline_id=pipeline.id,
            run_id=req.run_id,
            payload={
                "suggestions": suggestions,
                "rationale": rationale,
                "confidence": confidence,
                "context": req.context,
            },
            applied=False,
        )
        db.add(suggestion_record)
        db.commit()

    return OptimizeResp(
        suggestions=suggestions,
        rationale=rationale,
        confidence=confidence,
    )
