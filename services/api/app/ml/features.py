"""Feature engineering"""

from typing import Any
from sqlalchemy.orm import Session

from ..models.orm import Run, Step


def compute_features(run_id: str, db: Session) -> dict[str, Any]:
    """Compute feature vector from run and step data"""
    run = db.query(Run).filter(Run.run_id == run_id).first()
    if not run:
        return {}

    steps = db.query(Step).filter(Step.run_id == run_id).all()

    # Aggregate step metrics
    total_cpu_time = sum(s.cpu_time_s or 0 for s in steps)
    max_rss = max((s.rss_max_bytes or 0 for s in steps), default=0)
    total_io_read = sum(s.io_r_bytes or 0 for s in steps)
    total_io_write = sum(s.io_w_bytes or 0 for s in steps)
    total_cache_hits = sum(s.cache_hits for s in steps)
    total_cache_misses = sum(s.cache_misses for s in steps)

    cache_hit_ratio = (
        total_cache_hits / (total_cache_hits + total_cache_misses)
        if (total_cache_hits + total_cache_misses) > 0
        else 0.0
    )

    # Compute step durations
    step_durations = []
    for s in steps:
        if s.start_ts and s.end_ts:
            duration = (s.end_ts - s.start_ts).total_seconds()
            step_durations.append(duration)

    avg_step_duration = sum(step_durations) / len(step_durations) if step_durations else 0

    # Feature vector
    features = {
        # Static context
        "image": run.image or "unknown",
        "branch": run.branch or "unknown",
        "node": run.node or "unknown",
        # Requested resources
        "cpu_req": run.cpu_req or 4.0,
        "mem_req_gb": run.mem_req_gb or 8.0,
        "concurrency": run.concurrency or 4,
        # Observed telemetry
        "total_cpu_time_s": total_cpu_time,
        "max_rss_bytes": max_rss,
        "max_rss_gb": max_rss / (1024**3),
        "io_read_bytes": total_io_read,
        "io_write_bytes": total_io_write,
        "io_read_gb": total_io_read / (1024**3),
        "io_write_gb": total_io_write / (1024**3),
        "cache_hit_ratio": cache_hit_ratio,
        "cache_hits": total_cache_hits,
        "cache_misses": total_cache_misses,
        "num_steps": len(steps),
        "avg_step_duration_s": avg_step_duration,
        "artifact_bytes": run.artifact_bytes or 0,
        "artifact_mb": (run.artifact_bytes or 0) / (1024**2),
    }

    return features


def build_feature_matrix(runs: list[Run], db: Session) -> tuple[list[dict], list[float]]:
    """Build feature matrix X and labels y from runs"""
    X = []
    y = []

    for run in runs:
        features = compute_features(run.run_id, db)
        if features and run.duration_s:
            X.append(features)
            y.append(run.duration_s)

    return X, y
