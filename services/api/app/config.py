"""Configuration management"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    # Environment
    environment: str = "development"  # development, staging, production

    # API Configuration
    api_title: str = "InfraMind API"
    api_version: str = "0.1.0"
    api_key: str = "dev-key-change-in-production"
    api_host: str = "0.0.0.0"
    api_port: int = 8080

    # Database
    database_url: str = "postgresql://inframind:inframind_dev@localhost:5432/inframind"
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_password: str = ""

    # MinIO/S3
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    minio_bucket: str = "im-logs"

    # ML Configuration
    model_path: str = "./models"
    model_version: str = "v1"
    feature_cache_ttl: int = 3600  # 1 hour
    enable_ml_training: bool = True

    # Optimization Parameters
    safe_multiplier: float = 1.2
    exploration_rate: float = 0.15

    # Logging
    log_level: str = "INFO"

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 100
    rate_limit_burst: int = 20

    # CORS
    cors_origins: str = "*"  # Comma-separated list

    # Timeouts
    request_timeout: int = 30  # seconds

    # Workers
    uvicorn_workers: int = 1

    # Feature Flags
    enable_auto_scaling: bool = False
    enable_cost_tracking: bool = True
    enable_cache_optimization: bool = True

    # Monitoring
    slack_webhook_url: str = ""
    pagerduty_key: str = ""

    # Kubernetes
    k8s_namespace: str = "infra"
    k8s_in_cluster: bool = False
    k8s_api_server: str = ""

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == "development"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
