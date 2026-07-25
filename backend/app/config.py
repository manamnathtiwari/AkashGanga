"""Application configuration loaded from environment / .env."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AKASHGANGA_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    cors_origins: str = "http://localhost:3000,http://localhost:8080"

    jwt_secret: str = "dev-insecure-change-me-0000000000000000"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080  # 7 days

    database_url: str = "sqlite+aiosqlite:///./akashganga.db"
    upload_dir: str = "./uploads"

    solver_backend: str = "astrometry_net"  # or "mock"
    astrometry_api_key: str = ""
    astrometry_base_url: str = "https://nova.astrometry.net/api"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
