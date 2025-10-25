"""Configuration management"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    # API
    api_title: str = "InfraMind API"
    api_version: str = "0.1.0"
    api_key: str = "dev-key-change-in-production"

    # Database
    database_url: str = "postgresql://inframind:inframind_dev@localhost:5432/inframind"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # MinIO/S3
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    minio_bucket: str = "im-logs"

    # ML
    model_path: str = "./models"
    model_version: str = "v1"
    feature_cache_ttl: int = 3600  # 1 hour

    # Optimization
    safe_multiplier: float = 1.2
    exploration_rate: float = 0.15

    # Logging
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
