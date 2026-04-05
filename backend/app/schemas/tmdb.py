"""Pydantic response schemas for TMDb-sourced data."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class TMDbMovieResult(BaseModel):
    """Single movie item from a TMDb search result."""
    tmdb_id: int = Field(alias="id")
    title: str
    original_title: Optional[str] = None
    overview: Optional[str] = None
    release_date: Optional[str] = None
    year: Optional[int] = None
    poster_path: Optional[str] = None
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None
    vote_average: Optional[float] = None
    vote_count: Optional[int] = None
    popularity: Optional[float] = None
    genre_ids: list[int] = []

    model_config = {"populate_by_name": True}

    @classmethod
    def from_tmdb(cls, data: dict) -> "TMDbMovieResult":
        release = data.get("release_date") or ""
        year = int(release[:4]) if len(release) >= 4 else None
        return cls(
            id=data["id"],
            title=data.get("title", ""),
            original_title=data.get("original_title"),
            overview=data.get("overview"),
            release_date=release or None,
            year=year,
            poster_path=data.get("poster_path"),
            poster_url=data.get("poster_url"),
            backdrop_url=data.get("backdrop_url"),
            vote_average=data.get("vote_average"),
            vote_count=data.get("vote_count"),
            popularity=data.get("popularity"),
            genre_ids=data.get("genre_ids", []),
        )


class TMDbSearchResponse(BaseModel):
    """Paginated TMDb search response."""
    page: int
    total_results: int
    total_pages: int
    results: list[TMDbMovieResult]


class CastMember(BaseModel):
    name: str
    character: Optional[str] = None
    profile_url: Optional[str] = None


class TMDbGenre(BaseModel):
    id: int
    name: str


class TMDbMovieDetail(BaseModel):
    """Full movie detail returned by /search/tmdb/{tmdb_id}."""
    tmdb_id: int
    imdb_id: Optional[str] = None
    title: str
    original_title: Optional[str] = None
    overview: Optional[str] = None
    tagline: Optional[str] = None
    release_date: Optional[str] = None
    year: Optional[int] = None
    runtime: Optional[int] = None
    language: Optional[str] = None
    status: Optional[str] = None
    vote_average: Optional[float] = None
    vote_count: Optional[int] = None
    poster_path: Optional[str] = None
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None
    director: Optional[str] = None
    cast_top5: list[str] = []
    genres: list[TMDbGenre] = []

    @classmethod
    def from_tmdb(cls, data: dict) -> "TMDbMovieDetail":
        release = data.get("release_date") or ""
        year = int(release[:4]) if len(release) >= 4 else None
        return cls(
            tmdb_id=data["id"],
            imdb_id=data.get("imdb_id"),
            title=data.get("title", ""),
            original_title=data.get("original_title"),
            overview=data.get("overview"),
            tagline=data.get("tagline"),
            release_date=release or None,
            year=year,
            runtime=data.get("runtime"),
            language=data.get("original_language"),
            status=data.get("status"),
            vote_average=data.get("vote_average"),
            vote_count=data.get("vote_count"),
            poster_path=data.get("poster_path"),
            poster_url=data.get("poster_url"),
            backdrop_url=data.get("backdrop_url"),
            director=data.get("director"),
            cast_top5=data.get("cast_top5", []),
            genres=[
                TMDbGenre(id=g["id"], name=g["name"])
                for g in data.get("genres", [])
            ],
        )
