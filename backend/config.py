"""
Kashf Backend — Application Configuration
Reads settings from .env file using pydantic-settings.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────────────
    # Using asyncpg for Vercel Postgres / Supabase
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/kashf"

    # ── API Keys (optional) ──────────────────────────────────────────
    HIBP_API_KEY: str = ""
    SHODAN_API_KEY: str = ""

    # ── Local LLM ────────────────────────────────────────────────────
    LLM_MODEL_PATH: str = ""
    LLM_CONTEXT_SIZE: int = 2048
    LLM_MAX_TOKENS: int = 1024

    # ── CORS ─────────────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # ── Security ─────────────────────────────────────────────────────
    DATA_TTL_HOURS: int = 24

    # ── Scraper settings ─────────────────────────────────────────────
    SCRAPER_TIMEOUT: int = 30  # seconds per scraper
    MAX_CONCURRENT_SCRAPERS: int = 10
    USER_AGENTS: list[str] = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
    ]


# Singleton instance
settings = Settings()
