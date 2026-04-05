"""
GET  /api/v1/search?q=<query>&page=<n>   — search TMDb
GET  /api/v1/movies/popular              — popular movies
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import tmdb

router = APIRouter(prefix="/api/v1", tags=["search"])


@router.get("/search")
def search(
    q: str = Query(..., min_length=1, description="Movie title to search for"),
    page: int = Query(1, ge=1, le=500),
    db: Session = Depends(get_db),
) -> Any:
    """
    Search TMDb for movies matching the query string.
    Results are cached locally for 1 hour.
    """
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query must not be empty")
    return tmdb.search_movies(db, q.strip(), page=page)


@router.get("/movies/popular")
def popular(
    page: int = Query(1, ge=1, le=500),
    db: Session = Depends(get_db),
) -> Any:
    """Return the current TMDb popular movies list (cached 6 hours)."""
    return tmdb.get_popular_movies(db, page=page)


@router.get("/movies/{tmdb_id}/detail")
def movie_detail(
    tmdb_id: int,
    db: Session = Depends(get_db),
) -> Any:
    """
    Fetch full TMDb detail for a single movie.
    Includes cast, trailer links, keywords, release dates.
    Cached locally for 30 days.
    """
    try:
        return tmdb.get_movie_detail(db, tmdb_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"TMDb request failed: {exc}") from exc
