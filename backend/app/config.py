"""Application configuration loaded from environment variables / .env file."""
from __future__ import annotations

from functools import lru_cache
from typing import List, Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central settings object. Every value can be overridden via environment.

    Secrets such as JWT keys must be provided in production.
    """

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env", "../../.env"),
        env_prefix="AEGIS_",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Core ---
    app_name: str = "AEGIS"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: Literal["development", "test", "production"] = "development"
    api_v1_prefix: str = "/api/v1"
    host: str = "0.0.0.0"
    port: int = 8000

    # --- Database ---
    database_url: str = "sqlite:///./aegis.db"
    database_echo: bool = False
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # --- Redis / Celery ---
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    cache_default_ttl: int = 300

    # --- Auth / Security ---
    secret_key: str = "change-me-in-production-please-use-a-long-random-string"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_minutes: int = 10080  # 7 days
    password_reset_expire_minutes: int = 30
    bcrypt_rounds: int = 12

    # --- CORS ---
    cors_origins: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:8000",
            "http://localhost:8080",
            "http://127.0.0.1:8000",
        ]
    )

    # --- Rate limiting ---
    rate_limit_default: int = 60  # requests per minute
    rate_limit_scan: int = 10
    rate_limit_auth: int = 5
    rate_limit_admin: int = 120

    # --- URLs used by scanners ---
    http_timeout: float = 8.0
    max_redirects: int = 5
    max_remote_response_bytes: int = 2_000_000
    max_scan_recipients: int = 2000
    user_agent: str = (
        "AEGIS-TrustScan/1.0 (+https://aegis.local/security)"
        " Mozilla/5.0 (compatible) SecurityResearch/1.0"
    )
    require_https_scan: bool = False
    # Optional local MaxMind-compatible City MMDB path. When unset, no IP
    # geolocation occurs and the public map remains real-data-only.
    geoip_city_db: Optional[str] = None
    # Local loopback requests cannot have a real geolocation. This is used only
    # by the development server to exercise the moderation → map flow and is
    # never consulted in test or production environments.
    development_report_country: Optional[str] = "IR"

    # --- Deterministic evidence engine ---
    evidence_engine_version: str = "evidence-fusion-v2"
    # OCR is an acquisition layer only; no language model or learned classifier
    # is used by the prediction path.
    ocr_engine: Literal["auto", "tesseract", "easyocr", "none"] = "auto"
    # Optional absolute path to the Tesseract executable. This is especially
    # useful for native Windows installs where the installer is not on PATH.
    tesseract_cmd: Optional[str] = None

    # --- Uploads ---
    upload_dir: str = "./uploads"
    max_upload_mb: int = 15
    allowed_image_ext: set = {"png", "jpg", "jpeg", "webp", "bmp", "gif"}
    allowed_file_ext: set = {"pdf", "txt", "eml", "msg"}

    # --- Notifications ---
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from: str = "AEGIS <no-reply@aegis.local>"
    email_enabled: bool = False
    push_enabled: bool = True

    # --- PWA / Frontend ---
    frontend_origin: str = "http://localhost:8080"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value):
        if isinstance(value, str):
            return [o.strip() for o in value.split(",") if o.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def sqlalchemy_kwargs(self) -> dict:
        if self.database_url.startswith("sqlite"):
            return {"connect_args": {"check_same_thread": False}}
        return {
            "pool_size": self.database_pool_size,
            "max_overflow": self.database_max_overflow,
            "pool_pre_ping": True,
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
