from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.core.database import Base


class SyncLog(Base):
    """Tracks the last sync timestamp per device — used for delta sync."""
    __tablename__ = "sync_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    device_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    last_synced_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
