from sqlalchemy import String, Integer, Float, Text, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class Movie(Base):
    """Canonical movie record — sourced from TMDb or added manually."""
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, default=lambda: str(uuid.uuid4()), nullable=False)

    # TMDb identifiers
    tmdb_id: Mapped[int | None] = mapped_column(Integer, unique=True, nullable=True, index=True)
    imdb_id: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Core metadata
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    original_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    overview: Mapped[str | None] = mapped_column(Text, nullable=True)
    tagline: Mapped[str | None] = mapped_column(String(500), nullable=True)
    runtime: Mapped[int | None] = mapped_column(Integer, nullable=True)  # minutes
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Ratings from TMDb
    tmdb_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    tmdb_vote_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Poster / backdrop
    poster_path: Mapped[str | None] = mapped_column(String(500), nullable=True)   # TMDb path e.g. /abc.jpg
    backdrop_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    local_poster_path: Mapped[str | None] = mapped_column(String(500), nullable=True)  # cached local file

    # Director / cast (denormalised for simplicity in v1)
    director: Mapped[str | None] = mapped_column(String(300), nullable=True)
    cast_top5: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array string

    # Timestamps
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    genres: Mapped[list["MovieGenre"]] = relationship(back_populates="movie", cascade="all, delete-orphan")
    entries: Mapped[list["Entry"]] = relationship(back_populates="movie", cascade="all, delete-orphan")
