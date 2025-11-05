"""
Application configuration using Pydantic Settings.

Loads configuration from environment variables defined in .env file.
Uses type-safe configuration with Pydantic v2.
"""

from typing import Literal

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration."""

    # ==========================================================================
    # APPLICATION SETTINGS
    # ==========================================================================
    APP_NAME: str = Field(default="Face Attendance System", description="Application name")
    APP_VERSION: str = Field(default="0.1.0", description="Application version")
    DEBUG: bool = Field(default=True, description="Debug mode")
    ENVIRONMENT: Literal["development", "staging", "production"] = Field(
        default="development", description="Environment"
    )
    API_V1_PREFIX: str = Field(default="/api/v1", description="API v1 prefix")
    PROJECT_NAME: str = Field(default="Face Attendance API", description="Project name")

    # ==========================================================================
    # SERVER SETTINGS
    # ==========================================================================
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    RELOAD: bool = Field(default=True, description="Auto-reload on code changes")
    WORKERS: int = Field(default=4, description="Number of worker processes")

    # ==========================================================================
    # DATABASE CONFIGURATION
    # ==========================================================================
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/face_attendance",
        description="PostgreSQL async connection string",
    )
    SYNC_DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/face_attendance",
        description="PostgreSQL sync connection string for migrations",
    )
    DATABASE_ECHO: bool = Field(default=False, description="Log SQL queries")
    DATABASE_POOL_SIZE: int = Field(default=20, description="Database connection pool size")
    DATABASE_MAX_OVERFLOW: int = Field(default=10, description="Database max overflow")

    # ==========================================================================
    # REDIS CONFIGURATION
    # ==========================================================================
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    REDIS_PASSWORD: str = Field(default="", description="Redis password")
    REDIS_MAX_CONNECTIONS: int = Field(default=50, description="Max Redis connections")

    # Cache TTLs (seconds)
    CACHE_TTL_DETECTIONS: int = Field(default=3, description="Live detections cache TTL")
    CACHE_TTL_CAMERAS: int = Field(default=10, description="Cameras list cache TTL")
    CACHE_TTL_SYSTEM_SUMMARY: int = Field(default=15, description="System summary cache TTL")

    # ==========================================================================
    # JWT AUTHENTICATION
    # ==========================================================================
    SECRET_KEY: str = Field(
        default="your-secret-key-here-change-in-production",
        description="JWT secret key",
    )
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, description="Access token expiration")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=14, description="Refresh token expiration")

    # ==========================================================================
    # MINIO / S3 CONFIGURATION
    # ==========================================================================
    MINIO_ENDPOINT: str = Field(default="http://localhost:9000", description="MinIO endpoint")
    MINIO_ACCESS_KEY: str = Field(default="admin", description="MinIO access key")
    MINIO_SECRET_KEY: str = Field(default="password123", description="MinIO secret key")
    MINIO_BUCKET: str = Field(default="face-attendance-bucket", description="MinIO bucket")
    MINIO_SECURE: bool = Field(default=False, description="Use HTTPS for MinIO")
    MINIO_REGION: str = Field(default="us-east-1", description="MinIO region")
    PRESIGNED_URL_EXPIRATION: int = Field(default=86400, description="Signed URL expiration (seconds)")

    # ==========================================================================
    # CELERY CONFIGURATION
    # ==========================================================================
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/0", description="Celery broker URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/0", description="Celery result backend"
    )
    CELERY_TASK_SERIALIZER: str = Field(default="json", description="Celery task serializer")
    CELERY_RESULT_SERIALIZER: str = Field(default="json", description="Celery result serializer")
    CELERY_TIMEZONE: str = Field(default="UTC", description="Celery timezone")
    CELERY_TASK_TIME_LIMIT: int = Field(default=600, description="Celery task time limit (seconds)")
    CELERY_TASK_SOFT_TIME_LIMIT: int = Field(default=540, description="Celery task soft time limit")

    # ==========================================================================
    # FFMPEG CONFIGURATION
    # ==========================================================================
    FFMPEG_PATH: str = Field(default="/usr/bin/ffmpeg", description="FFmpeg path")
    FFPROBE_PATH: str = Field(default="/usr/bin/ffprobe", description="FFprobe path")
    SNAPSHOT_TIMEOUT: int = Field(default=30, description="Snapshot timeout (seconds)")
    SNAPSHOT_FORMAT: str = Field(default="jpg", description="Snapshot format")
    SNAPSHOT_QUALITY: int = Field(default=85, description="Snapshot quality (0-100)")

    # ==========================================================================
    # DETECTION PROVIDER CONFIGURATION
    # ==========================================================================
    DETECTION_PROVIDER_ENDPOINT: str = Field(
        default="http://localhost:8001/detect", description="Detection provider endpoint"
    )
    DETECTION_PROVIDER_API_KEY: str = Field(default="", description="Detection provider API key")
    DETECTION_PROVIDER_TIMEOUT: int = Field(default=30, description="Detection provider timeout")
    DETECTION_PROVIDER_RETRY_ATTEMPTS: int = Field(default=3, description="Retry attempts")

    # ==========================================================================
    # ODOO INTEGRATION
    # ==========================================================================
    ODOO_BASE_URL: str = Field(default="https://odoo.example.com", description="Odoo base URL")
    ODOO_DATABASE: str = Field(default="production_db", description="Odoo database")
    ODOO_USERNAME: str = Field(default="admin", description="Odoo username")
    ODOO_PASSWORD: str = Field(default="", description="Odoo password")
    ODOO_API_KEY: str = Field(default="", description="Odoo API key")
    ODOO_TIMEOUT: int = Field(default=60, description="Odoo timeout (seconds)")

    # ==========================================================================
    # CORS CONFIGURATION
    # ==========================================================================
    ALLOWED_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins",
    )
    ALLOW_CREDENTIALS: bool = Field(default=True, description="Allow credentials in CORS")
    ALLOWED_METHODS: list[str] = Field(
        default=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        description="Allowed HTTP methods",
    )
    ALLOWED_HEADERS: list[str] = Field(default=["*"], description="Allowed headers")

    # ==========================================================================
    # RATE LIMITING
    # ==========================================================================
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_PER_MINUTE: int = Field(default=120, description="Requests per minute")
    RATE_LIMIT_BURST: int = Field(default=20, description="Burst limit")

    # ==========================================================================
    # SECURITY SETTINGS
    # ==========================================================================
    ENCRYPTION_KEY: str = Field(
        default="your-encryption-key-here", description="Encryption key for sensitive data"
    )
    PASSWORD_MIN_LENGTH: int = Field(default=8, description="Minimum password length")
    PASSWORD_REQUIRE_UPPERCASE: bool = Field(default=True, description="Require uppercase")
    PASSWORD_REQUIRE_LOWERCASE: bool = Field(default=True, description="Require lowercase")
    PASSWORD_REQUIRE_DIGIT: bool = Field(default=True, description="Require digit")
    PASSWORD_REQUIRE_SPECIAL: bool = Field(default=False, description="Require special char")

    # ==========================================================================
    # LOGGING CONFIGURATION
    # ==========================================================================
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: Literal["json", "text"] = Field(default="json", description="Log format")
    LOG_FILE: str = Field(default="logs/app.log", description="Log file path")
    LOG_MAX_BYTES: int = Field(default=10485760, description="Max log file size")
    LOG_BACKUP_COUNT: int = Field(default=5, description="Log backup count")

    # ==========================================================================
    # FILE UPLOAD SETTINGS
    # ==========================================================================
    MAX_UPLOAD_SIZE: int = Field(default=10485760, description="Max upload size (bytes)")
    ALLOWED_IMAGE_EXTENSIONS: list[str] = Field(
        default=["jpg", "jpeg", "png"], description="Allowed image extensions"
    )
    MAX_FACE_IMAGES_PER_PROFILE: int = Field(default=5, description="Max face images per profile")

    # ==========================================================================
    # EXPORT SETTINGS
    # ==========================================================================
    EXPORT_EXPIRATION_DAYS: int = Field(default=7, description="Export file expiration (days)")
    EXPORT_MAX_ROWS: int = Field(default=100000, description="Max rows per export")

    # ==========================================================================
    # SYSTEM MONITORING
    # ==========================================================================
    METRICS_COLLECTION_INTERVAL: int = Field(default=60, description="Metrics collection interval")
    CAMERA_HEALTH_CHECK_INTERVAL: int = Field(default=120, description="Camera health check interval")
    DETECTION_HEALTH_CHECK_INTERVAL: int = Field(default=300, description="Detection health check")

    CPU_WARNING_THRESHOLD: int = Field(default=80, description="CPU warning threshold (%)")
    MEMORY_WARNING_THRESHOLD: int = Field(default=85, description="Memory warning threshold (%)")
    DISK_WARNING_THRESHOLD: int = Field(default=90, description="Disk warning threshold (%)")

    # ==========================================================================
    # DATA RETENTION
    # ==========================================================================
    DETECTIONS_RETENTION_DAYS: int = Field(default=90, description="Detections retention (days)")
    AUDIT_LOGS_RETENTION_DAYS: int = Field(default=365, description="Audit logs retention (days)")
    SYSTEM_METRICS_RETENTION_DAYS: int = Field(default=30, description="System metrics retention")
    EXPORT_JOBS_RETENTION_DAYS: int = Field(default=7, description="Export jobs retention (days)")

    # ==========================================================================
    # WEBSOCKET CONFIGURATION
    # ==========================================================================
    WEBSOCKET_PING_INTERVAL: int = Field(default=30, description="WebSocket ping interval")
    WEBSOCKET_PING_TIMEOUT: int = Field(default=10, description="WebSocket ping timeout")
    WEBSOCKET_MAX_CONNECTIONS: int = Field(default=1000, description="Max WebSocket connections")

    # ==========================================================================
    # LOCALIZATION
    # ==========================================================================
    DEFAULT_TIMEZONE: str = Field(default="UTC", description="Default timezone")
    DEFAULT_LANGUAGE: str = Field(default="en", description="Default language")

    # ==========================================================================
    # FEATURE FLAGS
    # ==========================================================================
    FEATURE_WEBSOCKET_ENABLED: bool = Field(default=True, description="Enable WebSocket")
    FEATURE_ODOO_SYNC_ENABLED: bool = Field(default=True, description="Enable Odoo sync")
    FEATURE_DETECTION_PROVIDER_ENABLED: bool = Field(default=True, description="Enable detection")
    FEATURE_EXPORT_PDF_ENABLED: bool = Field(default=True, description="Enable PDF export")
    FEATURE_FACE_REGISTRATION_ENABLED: bool = Field(default=True, description="Enable face registration")

    # ==========================================================================
    # DEVELOPMENT / TESTING
    # ==========================================================================
    TESTING: bool = Field(default=False, description="Test mode")
    SEED_DATABASE: bool = Field(default=False, description="Seed database on startup")
    SQL_ECHO: bool = Field(default=False, description="Echo SQL queries")

    class Config:
        """Pydantic config."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @validator("ALLOWED_ORIGINS", pre=True)
    @classmethod
    def validate_origins(cls, v: str | list[str]) -> list[str]:
        """Validate and parse origins."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @validator("ALLOWED_METHODS", pre=True)
    @classmethod
    def validate_methods(cls, v: str | list[str]) -> list[str]:
        """Validate and parse methods."""
        if isinstance(v, str):
            return [method.strip() for method in v.split(",")]
        return v

    @validator("ALLOWED_IMAGE_EXTENSIONS", pre=True)
    @classmethod
    def validate_extensions(cls, v: str | list[str]) -> list[str]:
        """Validate and parse extensions."""
        if isinstance(v, str):
            return [ext.strip().lower() for ext in v.split(",")]
        return [ext.lower() for ext in v]

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENVIRONMENT == "development"

    @property
    def is_testing(self) -> bool:
        """Check if running tests."""
        return self.TESTING


# Create global settings instance
settings = Settings()
