from sqlalchemy import String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class WatchEvent(Base):
    """Each time a user watches a movie — supports rewatch tracking."""
    __tablename__ = "watch_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, default=lambda: str(uuid.uuid4()), nullable=False)

    entry_id: Mapped[int] = mapped_column(ForeignKey("entries.id", ondelete="CASCADE"), nullable=False, index=True)
    watched_at: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)
    platform: Mapped[str | None] = mapped_column(String(100), nullable=True)  # Netflix, Cinema, etc.
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    entry: Mapped["Entry"] = relationship(back_populates="watch_events")
