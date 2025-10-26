"""Run ingestion endpoints"""

from datetime import datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..deps import get_db, verify_api_key
from ..models.orm import Pipeline, Run, Step, Feature
from ..models.schemas import RunIngestReq, RunIngestResp
from ..ml.features import extract_features

router = APIRouter()


@router.post("/runs", status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_api_key)])
async def ingest_run(req: RunIngestReq, db: Session = Depends(get_db)) -> RunIngestResp:
    """Ingest a complete run with all steps"""
    # Get or create pipeline
    pipeline = db.query(Pipeline).filter(Pipeline.name == req.pipeline).first()
    if not pipeline:
        pipeline = Pipeline(name=req.pipeline, repo="unknown")
        db.add(pipeline)
        db.flush()

    # Create run record
    run = Run(
        pipeline_id=pipeline.id,
        build_number=req.build_number,
        status=req.status,
        duration_s=req.duration_s,
        tool=req.tool,
        concurrency=req.concurrency,
        cpu_req=req.cpu_req,
        mem_req_gb=req.mem_req_gb,
        branch=req.git_branch,
        commit=req.git_sha,
        started_at=datetime.fromisoformat(req.start_time.replace('Z', '+00:00')),
        finished_at=datetime.fromisoformat(req.end_time.replace('Z', '+00:00')),
    )
    db.add(run)
    db.flush()

    # Create step records
    for step_data in req.steps:
        step = Step(
            run_id=run.id,
            name=step_data.name,
            start_ts=datetime.fromisoformat(step_data.start_time.replace('Z', '+00:00')),
            end_ts=datetime.fromisoformat(step_data.end_time.replace('Z', '+00:00')),
            duration_s=step_data.duration_s,
            cpu_time_s=step_data.cpu_usage_pct,
            rss_max_bytes=step_data.rss_max_bytes,
            io_r_bytes=step_data.io_r_bytes,
            io_w_bytes=step_data.io_w_bytes,
            exit_code=step_data.exit_code,
        )
        db.add(step)

    # Extract and store features
    features = extract_features(run, req.steps)
    feature_record = Feature(
        run_id=run.id,
        tool=req.tool,
        max_rss_gb=features.get("max_rss_gb", 0),
        total_io_gb=features.get("total_io_gb", 0),
        num_steps=features.get("num_steps", 0),
        avg_step_duration_s=features.get("avg_step_duration_s", 0),
        max_step_duration_s=features.get("max_step_duration_s", 0),
        total_cpu_s=features.get("total_cpu_s", 0),
    )
    db.add(feature_record)

    db.commit()

    return RunIngestResp(status="ingested", run_id=run.id)
