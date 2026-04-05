from datetime import datetime

from sqlalchemy import Column, Integer, String, Date, Float, Text, DateTime

from app.core.database import Base


class Movie(Base):
    __tablename__ = "movies"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    tmdb_id        = Column(Integer, unique=True, nullable=False, index=True)
    imdb_id        = Column(String(20), nullable=True)
    title          = Column(String(500), nullable=False)
    original_title = Column(String(500), nullable=True)
    overview       = Column(Text, nullable=True)
    release_date   = Column(Date, nullable=True)
    runtime        = Column(Integer, nullable=True)
    poster_path    = Column(String(300), nullable=True)   # raw TMDb path
    backdrop_path  = Column(String(300), nullable=True)
    vote_average   = Column(Float, nullable=True)
    tagline        = Column(Text, nullable=True)
    language       = Column(String(10), nullable=True)
    tmdb_data_json = Column(Text, nullable=True)          # full raw JSON snapshot
    cached_at      = Column(DateTime, default=datetime.utcnow)
    updated_at     = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
