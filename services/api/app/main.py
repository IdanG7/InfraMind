"""FastAPI main application"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import builds, features, health, optimize
from .storage.postgres import engine, Base
from .middleware.rate_limit import setup_rate_limiting
from .middleware.metrics import metrics_middleware, metrics_endpoint


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager"""
    # Startup: Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    lifespan=lifespan,
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Prometheus metrics middleware
app.middleware("http")(metrics_middleware)

# Setup rate limiting (uses Redis for distributed rate limiting)
setup_rate_limiting(app)

# Routers
app.include_router(health.router, tags=["health"])
app.include_router(builds.router, prefix="/builds", tags=["builds"])
app.include_router(optimize.router, tags=["optimize"])
app.include_router(features.router, prefix="/features", tags=["features"])

# Prometheus metrics endpoint
app.add_api_route("/metrics", metrics_endpoint, methods=["GET"], include_in_schema=False)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint"""
    return {
        "service": "InfraMind API",
        "version": settings.api_version,
        "docs": "/docs",
    }
