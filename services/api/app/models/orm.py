"""SQLAlchemy ORM models"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Pipeline(Base):
    """Pipeline model"""

    __tablename__ = "pipelines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    repo = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    runs = relationship("Run", back_populates="pipeline")
    suggestions = relationship("Suggestion", back_populates="pipeline")


class Run(Base):
    """Build run model"""

    __tablename__ = "runs"

    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(Integer, ForeignKey("pipelines.id"), nullable=False)
    run_id = Column(String, unique=True, nullable=False, index=True)
    status = Column(String, nullable=False)  # success, failure, aborted
    duration_s = Column(Float)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime)
    image = Column(String)
    node = Column(String)
    cpu_req = Column(Float)
    mem_req_gb = Column(Float)
    concurrency = Column(Integer)
    artifact_bytes = Column(Integer, default=0)
    cost_cents = Column(Float)
    branch = Column(String)
    commit = Column(String)
    git = Column(String)

    pipeline = relationship("Pipeline", back_populates="runs")
    steps = relationship("Step", back_populates="run")
    features = relationship("Feature", back_populates="run")
    suggestions = relationship("Suggestion", back_populates="run")

    __table_args__ = (Index("idx_pipeline_started", "pipeline_id", "started_at"),)


class Step(Base):
    """Build step model"""

    __tablename__ = "steps"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, ForeignKey("runs.run_id"), nullable=False)
    stage = Column(String, nullable=False)
    step = Column(String, nullable=False)
    span_id = Column(String)
    start_ts = Column(DateTime)
    end_ts = Column(DateTime)
    cpu_time_s = Column(Float)
    rss_max_bytes = Column(BigInteger)
    io_r_bytes = Column(BigInteger)
    io_w_bytes = Column(BigInteger)
    cache_hits = Column(Integer, default=0)
    cache_misses = Column(Integer, default=0)

    run = relationship("Run", back_populates="steps")

    __table_args__ = (Index("idx_run_stage_step", "run_id", "stage", "step"),)


class Feature(Base):
    """Feature vector model"""

    __tablename__ = "features"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, ForeignKey("runs.run_id"), nullable=False, index=True)
    vector = Column(JSON, nullable=False)
    label = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("Run", back_populates="features")


class Suggestion(Base):
    """Optimization suggestion model"""

    __tablename__ = "suggestions"

    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(Integer, ForeignKey("pipelines.id"), nullable=False)
    run_id = Column(String, ForeignKey("runs.run_id"), nullable=True)
    payload = Column(JSON, nullable=False)
    applied = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    pipeline = relationship("Pipeline", back_populates="suggestions")
    run = relationship("Run", back_populates="suggestions")


class Model(Base):
    """ML model metadata"""

    __tablename__ = "models"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String, unique=True, nullable=False)
    algo = Column(String, nullable=False)
    metrics = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
