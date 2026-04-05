from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class EntryTag(Base):
    __tablename__ = "entry_tags"

    entry_id: Mapped[int] = mapped_column(ForeignKey("entries.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)

    entry: Mapped["Entry"] = relationship(back_populates="tags")
    tag: Mapped["Tag"] = relationship(back_populates="entries")
