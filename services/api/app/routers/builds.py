"""Build tracking endpoints"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..deps import get_db
from ..models.orm import Pipeline, Run, Step
from ..models.schemas import BuildStartReq, BuildStepReq, BuildCompleteReq

router = APIRouter()


@router.post("/start")
async def build_start(req: BuildStartReq, db: Session = Depends(get_db)) -> dict[str, bool]:
    """Record build start"""
    # Get or create pipeline
    pipeline = db.query(Pipeline).filter(Pipeline.name == req.pipeline).first()
    if not pipeline:
        pipeline = Pipeline(name=req.pipeline, repo=req.git or "unknown")
        db.add(pipeline)
        db.flush()

    # Create run record
    run = Run(
        pipeline_id=pipeline.id,
        run_id=req.run_id,
        status="running",
        image=req.image,
        node=req.k8s_node,
        cpu_req=req.requested_resources.get("cpu"),
        mem_req_gb=req.requested_resources.get("mem_gb"),
        concurrency=req.requested_resources.get("concurrency"),
        branch=req.branch,
        commit=req.commit,
        git=req.git,
    )
    db.add(run)
    db.commit()

    return {"ok": True}


@router.post("/step")
async def build_step(req: BuildStepReq, db: Session = Depends(get_db)) -> dict[str, bool]:
    """Record build step event"""
    # Find or create step
    step = (
        db.query(Step)
        .filter(
            Step.run_id == req.run_id,
            Step.stage == req.stage,
            Step.step == req.step,
        )
        .first()
    )

    if req.event == "start":
        if not step:
            step = Step(
                run_id=req.run_id,
                stage=req.stage,
                step=req.step,
                span_id=req.span_id,
                start_ts=req.timestamp,
            )
            db.add(step)
        else:
            step.start_ts = req.timestamp
            step.span_id = req.span_id

    elif req.event == "stop":
        if not step:
            raise HTTPException(status_code=404, detail="Step not found")

        step.end_ts = req.timestamp
        step.cpu_time_s = req.counters.get("cpu_time_s")
        step.rss_max_bytes = req.counters.get("rss_max_bytes")
        step.io_r_bytes = req.counters.get("io_r_bytes")
        step.io_w_bytes = req.counters.get("io_w_bytes")
        step.cache_hits = req.counters.get("cache_hits", 0)
        step.cache_misses = req.counters.get("cache_misses", 0)

    db.commit()
    return {"ok": True}


@router.post("/complete")
async def build_complete(req: BuildCompleteReq, db: Session = Depends(get_db)) -> dict[str, bool]:
    """Record build completion"""
    run = db.query(Run).filter(Run.run_id == req.run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    run.status = req.status
    run.duration_s = req.duration_s
    run.finished_at = datetime.utcnow()

    # Calculate artifact size
    run.artifact_bytes = sum(a.get("size", 0) for a in req.artifacts)

    db.commit()

    # Trigger feature computation and model training (async in production)
    # TODO: Add to task queue

    return {"ok": True}
