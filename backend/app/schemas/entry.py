from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from typing import Optional, Any
from datetime import datetime
from app.schemas.movie import MovieOut


# ── Watch Events ──────────────────────────────────────────────────────────────

class WatchEventCreate(BaseModel):
    watched_at: Optional[datetime] = None
    platform: Optional[str] = None
    note: Optional[str] = None


class WatchEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    uuid: str
    watched_at: Optional[datetime] = None
    platform: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime


# ── Tags ──────────────────────────────────────────────────────────────────────

class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


# ── Entries ───────────────────────────────────────────────────────────────────

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
    def rating_range(cls, v: Optional[float]) -> Optional[float]:
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

    @field_validator("rating")
    @classmethod
    def rating_range(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0.5 <= v <= 10.0):
            raise ValueError("Rating must be between 0.5 and 10.0")
        return v


class EntryOut(BaseModel):
    """
    EntryOut serialises the Entry ORM object.

    The `tags` field on the ORM Entry is a list of EntryTag join objects
    (each has a `.tag` attribute pointing to the real Tag).  Pydantic cannot
    auto-map that to list[TagOut], so we flatten it with a model_validator.
    """
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

    @model_validator(mode="before")
    @classmethod
    def flatten_entry_tags(cls, data: Any) -> Any:
        """
        ORM gives us a list of EntryTag objects on `.tags`.
        Unwrap each to its nested `.tag` so Pydantic sees list[Tag].
        """
        # Only applies when building from an ORM instance
        if hasattr(data, "tags"):
            raw_tags = data.tags  # list[EntryTag]
            if raw_tags and hasattr(raw_tags[0], "tag"):
                # Replace with a temporary __dict__ copy so we don't mutate the ORM
                class _Proxy:
                    pass
                proxy = _Proxy()
                proxy.__dict__.update(data.__dict__)
                # Build a plain list of Tag objects
                proxy.tags = [et.tag for et in raw_tags]
                return proxy
        return data
