"""FastAPI main application"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import builds, features, health, optimize
from .storage.postgres import engine, Base


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

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router, tags=["health"])
app.include_router(builds.router, prefix="/builds", tags=["builds"])
app.include_router(optimize.router, tags=["optimize"])
app.include_router(features.router, prefix="/features", tags=["features"])


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint"""
    return {
        "service": "InfraMind API",
        "version": settings.api_version,
        "docs": "/docs",
    }
