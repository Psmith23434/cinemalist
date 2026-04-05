from __future__ import annotations

from pydantic import BaseModel, ConfigDict, computed_field
from typing import Optional, List
from datetime import datetime


class GenreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    tmdb_id: Optional[int] = None


class MovieBase(BaseModel):
    title: str
    original_title: Optional[str] = None
    year:           Optional[int] = None
    overview:       Optional[str] = None
    tagline:        Optional[str] = None
    runtime:        Optional[int] = None
    language:       Optional[str] = None
    director:       Optional[str] = None
    tmdb_id:        Optional[int] = None
    imdb_id:        Optional[str] = None
    poster_path:    Optional[str] = None
    backdrop_path:  Optional[str] = None
    tmdb_rating:    Optional[float] = None
    tmdb_vote_count: Optional[int] = None
    status:         Optional[str] = None
    cast_top5:      Optional[str] = None   # JSON string "[\"Actor A\", ...]"


class MovieCreate(MovieBase):
    # Optional list of TMDb genre IDs — used when manually adding a movie
    # without going through the /search/tmdb/import route.
    tmdb_genre_ids: Optional[List[int]] = None


class MovieOut(MovieBase):
    model_config = ConfigDict(from_attributes=True)

    id:                int
    uuid:              str
    genres:            list[GenreOut] = []
    local_poster_path: Optional[str] = None
    created_at:        datetime
    updated_at:        datetime

    @computed_field  # type: ignore[misc]
    @property
    def poster_url(self) -> Optional[str]:
        """Best available poster URL: local cache → TMDb CDN → None."""
        if self.local_poster_path:
            return f"/media/{self.local_poster_path}"
        if self.poster_path:
            return f"https://image.tmdb.org/t/p/w500{self.poster_path}"
        return None
