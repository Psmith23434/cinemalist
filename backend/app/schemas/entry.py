from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from .movie import MovieSummary
from .watch_event import WatchEventRead
from .tag import TagRead


class EntryBase(BaseModel):
    rating: Optional[float] = Field(None, ge=0.5, le=10.0)
    notes: Optional[str] = None
    review: Optional[str] = None
    is_favorite: bool = False
    is_watchlisted: bool = False
    watched: bool = True
    first_watched_at: Optional[datetime] = None
    last_watched_at: Optional[datetime] = None


class EntryCreate(EntryBase):
    """Create an entry — requires a movie_id (movie must already exist)."""
    movie_id: int


class EntryUpdate(BaseModel):
    """All fields optional for PATCH."""
    rating: Optional[float] = Field(None, ge=0.5, le=10.0)
    notes: Optional[str] = None
    review: Optional[str] = None
    is_favorite: Optional[bool] = None
    is_watchlisted: Optional[bool] = None
    watched: Optional[bool] = None
    first_watched_at: Optional[datetime] = None
    last_watched_at: Optional[datetime] = None


class EntryRead(EntryBase):
    id: int
    uuid: str
    movie_id: int
    movie: Optional[MovieSummary] = None
    watch_events: List[WatchEventRead] = []
    tags: List[TagRead] = []
    created_at: datetime
    updated_at: datetime
    # Bug 13 fix: sync_pull returns soft-deleted entries so Android can
    # process deletions. Without this field the client cannot distinguish
    # a deleted entry from an active one — ghost entries would accumulate.
    deleted_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
