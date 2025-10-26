"""Pytest configuration and fixtures"""

import os

# Set test environment variables before any app imports
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"  # Use different DB for tests
os.environ["API_KEY"] = "dev-key-change-in-production"
os.environ["ENVIRONMENT"] = "test"
os.environ["LOG_LEVEL"] = "WARNING"
