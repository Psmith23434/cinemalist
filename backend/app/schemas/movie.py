from __future__ import annotations
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime
from .genre import GenreRead


class MovieBase(BaseModel):
    title: str
    original_title: Optional[str] = None
    year: Optional[int] = None
    overview: Optional[str] = None
    tagline: Optional[str] = None
    runtime: Optional[int] = None
    language: Optional[str] = None
    status: Optional[str] = None
    tmdb_id: Optional[int] = None
    imdb_id: Optional[str] = None
    tmdb_rating: Optional[float] = None
    tmdb_vote_count: Optional[int] = None
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    director: Optional[str] = None
    cast_top5: Optional[str] = None  # JSON string


class MovieCreate(MovieBase):
    """Used when manually creating a movie or importing from TMDb."""
    pass


class MovieSummary(BaseModel):
    """Lightweight representation for lists/grids."""
    id: int
    uuid: str
    title: str
    year: Optional[int] = None
    poster_path: Optional[str] = None
    local_poster_path: Optional[str] = None
    tmdb_rating: Optional[float] = None
    director: Optional[str] = None

    model_config = {"from_attributes": True}


class MovieRead(MovieBase):
    id: int
    uuid: str
    local_poster_path: Optional[str] = None
    genres: List[GenreRead] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
