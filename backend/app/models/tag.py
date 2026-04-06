from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)

    # Many-to-many back-reference — gives list[Entry] directly
    entries: Mapped[list["Entry"]] = relationship(
        "Entry",
        secondary="entry_tags",
        back_populates="tags",
    )
