"""Application configuration from environment variables."""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    secret_key: str
    ingest_api_key: str
    database_url: str
    cors_origins: str
    display_timezone: str = "Asia/Manila"
    image_storage_path: str = "/data/images"
    image_storage_backend: str = "local"
    image_fetch_timeout_seconds: int = Field(default=10, validation_alias="IMAGE_FETCH_TIMEOUT_SECONDS")
    image_max_bytes: int = Field(default=5_000_000, validation_alias="IMAGE_MAX_BYTES")
    image_signed_url_expire_minutes: int = Field(
        default=60,
        validation_alias="IMAGE_SIGNED_URL_EXPIRE_MINUTES",
    )
    cv_image_url_allowlist: str = Field(default="", validation_alias="CV_IMAGE_URL_ALLOWLIST")
    log_level: str = "INFO"
    public_api_url: str = Field(default="http://localhost:8000", validation_alias="PUBLIC_API_URL")
    dev_auth_bypass: bool = Field(default=False, validation_alias="DEV_AUTH_BYPASS")
    report_logo_url: str | None = Field(default=None, validation_alias="REPORT_LOGO_URL")

    @field_validator("display_timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"Unknown IANA timezone: {value}") from exc
        return value

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def cv_image_url_allowlist_prefixes(self) -> list[str]:
        return [prefix.strip() for prefix in self.cv_image_url_allowlist.split(",") if prefix.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
