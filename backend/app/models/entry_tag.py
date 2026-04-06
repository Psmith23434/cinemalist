from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class EntryTag(Base):
    """Pure join table — no extra columns, no relationship() needed.

    Entry.tags and Tag.entries both use secondary='entry_tags', so
    SQLAlchemy manages this table automatically.  Adding relationship()
    declarations here would conflict with the secondary= back-references
    and cause KeyError / MissingGreenlet errors.
    """
    __tablename__ = "entry_tags"

    entry_id: Mapped[int] = mapped_column(
        ForeignKey("entries.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )
