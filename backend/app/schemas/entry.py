from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from datetime import datetime
from app.schemas.movie import MovieOut


class WatchEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    uuid: str
    watched_at: Optional[datetime] = None
    platform: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime


class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class EntryCreate(BaseModel):
    movie_id: int
    rating: Optional[float] = None
    notes: Optional[str] = None
    review: Optional[str] = None
    is_favorite: bool = False
    is_watchlisted: bool = False
    watched: bool = True
    first_watched_at: Optional[datetime] = None
    tag_names: list[str] = []

    @field_validator("rating")
    @classmethod
    def rating_range(cls, v):
        if v is not None and not (0.5 <= v <= 10.0):
            raise ValueError("Rating must be between 0.5 and 10.0")
        return v


class EntryUpdate(BaseModel):
    rating: Optional[float] = None
    notes: Optional[str] = None
    review: Optional[str] = None
    is_favorite: Optional[bool] = None
    is_watchlisted: Optional[bool] = None
    watched: Optional[bool] = None
    first_watched_at: Optional[datetime] = None
    tag_names: Optional[list[str]] = None


class EntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    uuid: str
    movie_id: int
    rating: Optional[float] = None
    notes: Optional[str] = None
    review: Optional[str] = None
    is_favorite: bool
    is_watchlisted: bool
    watched: bool
    first_watched_at: Optional[datetime] = None
    last_watched_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    movie: Optional[MovieOut] = None
    watch_events: list[WatchEventOut] = []
    tags: list[TagOut] = []
