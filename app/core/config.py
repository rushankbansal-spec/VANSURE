"""Application configuration module using Pydantic Settings."""

import secrets
from functools import lru_cache
from typing import Any, Literal

from pydantic import (
    BaseModel,
    Field,
    PostgresDsn,
    RedisDsn,
    computed_field,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseModel):
    """Database configuration."""

    url: PostgresDsn
    echo: bool = False
    pool_size: int = 20
    max_overflow: int = 40
    pool_timeout: int = 30
    pool_pre_ping: bool = True
    connect_args: dict[str, Any] = {
        "application_name": "vansure",
    }

    @computed_field
    @property
    def async_url(self) -> str:
        """Return async version of the URL."""
        return str(self.url).replace("postgresql://", "postgresql+asyncpg://", 1)


class RedisSettings(BaseModel):
    """Redis configuration."""

    dsn: RedisDsn | str
    decode_responses: bool = True
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True


class JWTSettings(BaseModel):
    """JWT authentication configuration."""

    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(64))
    algorithm: str = "HS256"
    access_token_expiration: int = 900  # 15 minutes
    refresh_token_expiration: int = 604800  # 7 days
    audience: str = "vansure"
    issuer: str = "vansure-api"


class PasswordSettings(BaseModel):
    """Argon2id password hashing configuration."""

    # Memory cost in KiB (64 MB default)
    memory_cost: int = 65536
    # Time cost (iterations)
    time_cost: int = 3
    # Parallelism (threads)
    parallelism: int = 4
    # Salt length
    salt_length: int = 16
    # Hash length
    hash_length: int = 32


class RateLimitSettings(BaseModel):
    """Rate limiting configuration."""

    ttl: int = 60000  # 1 minute in ms
    max_auth_requests: int = 5
    max_gps_requests: int = 20
    max_general: int = 100
    # Burst settings
    window_size: int = 60  # seconds


class SecuritySettings(BaseModel):
    """Security configuration."""

    cors_origins: list[str] = []
    cors_allow_credentials: bool = True
    cors_max_age: int = 3600
    # HTTPS only in production
    cookie_secure: bool = True
    cookie_httponly: bool = True
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    # Content Security Policy
    content_security_policy: str | None = None


class LoggingSettings(BaseModel):
    """Logging configuration."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    format: Literal["json", "plain"] = "json"
    # Fields to trim/sensitive not to log
    trimmed_fields: list[str] = [
        "password",
        "passwordHash",
        "token",
        "refreshToken",
        "accessToken",
        "apiKey",
        "secret",
        "credential",
    ]


class FeatureFlags(BaseModel):
    """Feature flags configuration."""

    enable_websocket: bool = True
    enable_push_notifications: bool = True
    enable_csv_export: bool = True
    enable_mqtt: bool = False
    enable_otp: bool = False
    enable_ai_eta: bool = False
    enable_route_optimization: bool = False


class SchoolSettings(BaseModel):
    """School-specific settings defaults."""

    timezone: str = "UTC"
    language: str = "en"
    academic_year_format: str = "%Y-%m-%d"
    working_hours_start: str = "06:00:00"
    working_hours_end: str = "18:00:00"
    working_days: list[int] = [1, 2, 3, 4, 5]  # Mon-Fri


class GPSConfig(BaseModel):
    """GPS tracking configuration."""

    ttl_seconds: int = 300  # 5 minutes
    batch_size: int = 100
    archive_interval_seconds: int = 300
    max_accuracy_meters: float = 50.0
    stale_threshold_seconds: int = 120  # 2 minutes


class NotificationSettings(BaseModel):
    """Notification configuration."""

    quiet_hours_start: str = "22:00:00"
    quiet_hours_end: str = "08:00:00"
    max_retries: int = 3
    retry_backoff_base: int = 2  # Exponential: 2, 4, 8 seconds
    delivery_timeout: int = 300  # 5 minutes
    dead_letter_queue: bool = True


class IdempotencyConfig(BaseModel):
    """Idempotency configuration."""

    ttl_seconds: int = 86400  # 24 hours
    enabled: bool = True


class BillingSettings(BaseModel):
    """Billing configuration."""

    currency: str = "USD"
    tax_enabled: bool = False
    late_fee_percentage: float = 1.5
    late_fee_days: int = 7


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
        revalidate_on_startup=True,
    )

    # Core
    app_name: str = "VanSure"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4

    # Database
    database: DatabaseSettings

    # Redis
    redis: RedisSettings

    # Security
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    password: PasswordSettings = Field(default_factory=PasswordSettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)

    # Logging
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    # Features
    features: FeatureFlags = Field(default_factory=FeatureFlags)

    # Modules
    school_settings: SchoolSettings = Field(default_factory=SchoolSettings)
    gps_config: GPSConfig = Field(default_factory=GPSConfig)
    notification_settings: NotificationSettings = Field(default_factory=NotificationSettings)
    idempotency: IdempotencyConfig = Field(default_factory=IdempotencyConfig)
    billing: BillingSettings = Field(default_factory=BillingSettings)

    # External services (optional adapters)
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None

    mqtt_broker: str | None = None
    mqtt_port: int = 1883
    mqtt_username: str | None = None
    mqtt_password: str | None = None

    # Monitoring
    sentry_dsn: str | None = None
    prometheus_enabled: bool = False
    metrics_path: str = "/metrics"

    @computed_field
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"

    @computed_field
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


def get_database_settings() -> DatabaseSettings:
    """Get database settings."""
    return get_settings().database


def get_redis_settings() -> RedisSettings:
    """Get Redis settings."""
    return get_settings().redis


def get_jwt_settings() -> JWTSettings:
    """Get JWT settings."""
    return get_settings().jwt


def get_rate_limit_settings() -> RateLimitSettings:
    """Get rate limit settings."""
    return get_settings().rate_limit


def get_security_settings() -> SecuritySettings:
    """Get security settings."""
    return get_settings().security


def get_logging_settings() -> LoggingSettings:
    """Get logging settings."""
    return get_settings().logging