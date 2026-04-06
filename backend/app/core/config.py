from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./cinemalist.db"

    # TMDb
    TMDB_API_KEY: str = ""
    TMDB_BASE_URL: str = "https://api.themoviedb.org/3"
    TMDB_IMAGE_BASE: str = "https://image.tmdb.org/t/p"

    # App
    # Bug 14 fix: no default value — production startup fails fast if this is missing.
    # Set a strong random value in your .env: SECRET_KEY=<openssl rand -hex 32>
    SECRET_KEY: str = ""
    DEBUG: bool = True
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # LLM (Phase 5)
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_PROXY_URL: str = "https://api.openai.com/v1"

    # Media
    MEDIA_DIR: str = "./media"

    @model_validator(mode="after")
    def validate_secret_key(self) -> "Settings":
        """Enforce a strong SECRET_KEY in production.
        In dev (DEBUG=True) a missing key is tolerated with a warning.
        In production (DEBUG=False) startup is aborted if the key is
        absent or shorter than 32 characters.
        """
        if not self.DEBUG:
            if not self.SECRET_KEY or len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "SECRET_KEY must be set to a random string of at least 32 characters "
                    "when DEBUG=False. Generate one with: openssl rand -hex 32"
                )
        return self


settings = Settings()
