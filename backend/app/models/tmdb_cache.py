from sqlalchemy import String, Integer, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.core.database import Base


class TmdbCache(Base):
    """Caches raw TMDb API responses to avoid redundant calls."""
    __tablename__ = "tmdb_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cache_key: Mapped[str] = mapped_column(String(300), unique=True, nullable=False, index=True)
    data_json: Mapped[str] = mapped_column(Text, nullable=False)  # raw JSON string
    fetched_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)
