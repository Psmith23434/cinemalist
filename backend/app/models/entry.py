from sqlalchemy import String, Integer, Float, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class Entry(Base):
    """
    A user's personal record for a movie.
    One Entry per movie — watch history lives in WatchEvent.
    """
    __tablename__ = "entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, default=lambda: str(uuid.uuid4()), nullable=False)

    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True)

    # User data
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0.5 – 10.0
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    review: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_watchlisted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    watched: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # First watch date (convenience — full history in WatchEvent)
    first_watched_at: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)
    last_watched_at: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)

    # Sync fields
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)  # soft delete

    # Relationships
    movie: Mapped["Movie"] = relationship(back_populates="entries")
    watch_events: Mapped[list["WatchEvent"]] = relationship(back_populates="entry", cascade="all, delete-orphan")
    tags: Mapped[list["EntryTag"]] = relationship(back_populates="entry", cascade="all, delete-orphan")
    list_items: Mapped[list["ListItem"]] = relationship(back_populates="entry", cascade="all, delete-orphan")
