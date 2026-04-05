from sqlalchemy import Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ListItem(Base):
    __tablename__ = "list_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    list_id: Mapped[int] = mapped_column(ForeignKey("movie_lists.id", ondelete="CASCADE"), nullable=False)
    entry_id: Mapped[int] = mapped_column(ForeignKey("entries.id", ondelete="CASCADE"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0)  # for ordered lists
    added_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    list: Mapped["MovieList"] = relationship(back_populates="items")
    entry: Mapped["Entry"] = relationship(back_populates="list_items")
