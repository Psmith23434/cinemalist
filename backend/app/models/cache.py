from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Text

from app.core.database import Base


class ApiCache(Base):
    __tablename__ = "tmdb_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cache_key = Column(String(255), unique=True, nullable=False, index=True)
    data_json = Column(Text, nullable=False)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
