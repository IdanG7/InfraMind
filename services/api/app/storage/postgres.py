"""PostgreSQL storage"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..config import settings
from ..models.orm import Base

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def get_recent_runs(pipeline_name: str, limit: int = 100) -> list[dict]:
    """Get recent runs for a pipeline"""
    from ..models.orm import Run, Pipeline

    session = SessionLocal()
    try:
        pipeline = session.query(Pipeline).filter(Pipeline.name == pipeline_name).first()
        if not pipeline:
            return []

        runs = (
            session.query(Run)
            .filter(Run.pipeline_id == pipeline.id, Run.status == "success")
            .order_by(Run.started_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "run_id": r.run_id,
                "duration_s": r.duration_s,
                "cpu_req": r.cpu_req,
                "mem_req_gb": r.mem_req_gb,
                "concurrency": r.concurrency,
                "started_at": r.started_at,
            }
            for r in runs
        ]
    finally:
        session.close()
