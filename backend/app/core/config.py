from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # TMDb
    TMDB_API_KEY: str = ""
    TMDB_BASE_URL: str = "https://api.themoviedb.org/3"
    TMDB_IMAGE_BASE: str = "https://image.tmdb.org/t/p/w500"

    # Database
    DATABASE_URL: str = "sqlite:///./cinemalist.db"

    # Media / file storage
    MEDIA_DIR: str = "./media"

    # App
    SECRET_KEY: str = "change-me-in-production"
    DEBUG: bool = True

    # LLM proxy (Phase 5 — optional for now)
    LLM_PROXY_URL: str = ""
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
