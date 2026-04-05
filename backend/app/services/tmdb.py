"""
TMDb API service — search, fetch details, download posters, cache layer.
All external HTTP calls go through this module.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
CACHE_TTL_DAYS = 30          # re-fetch movie detail after this many days
SEARCH_CACHE_HOURS = 1       # re-fetch search results after this many hours


# ---------------------------------------------------------------------------
# Low-level HTTP helper
# ---------------------------------------------------------------------------
def _get(path: str, params: dict | None = None) -> dict:
    """Make an authenticated GET request to the TMDb v3 API."""
    url = f"{BASE_URL}{path}"
    headers = {
        "Authorization": f"Bearer {settings.TMDB_API_KEY}",
        "Accept": "application/json",
    }
    base_params = {"language": "en-US"}
    if params:
        base_params.update(params)

    with httpx.Client(timeout=10.0) as client:
        response = client.get(url, headers=headers, params=base_params)
        response.raise_for_status()
        return response.json()


# ---------------------------------------------------------------------------
# Cache helpers  (uses app.models.ApiCache)
# ---------------------------------------------------------------------------
def _get_cache(db: Session, key: str) -> dict | None:
    """Return unexpired cached JSON or None."""
    from app.models.cache import ApiCache  # local import avoids circular deps

    row = db.query(ApiCache).filter(ApiCache.cache_key == key).first()
    if row and row.expires_at and row.expires_at > datetime.utcnow():
        return json.loads(row.data_json)
    return None


def _set_cache(db: Session, key: str, data: dict, ttl_hours: float = CACHE_TTL_DAYS * 24) -> None:
    """Upsert a cache entry."""
    from app.models.cache import ApiCache

    expires = datetime.utcnow() + timedelta(hours=ttl_hours)
    row = db.query(ApiCache).filter(ApiCache.cache_key == key).first()
    if row:
        row.data_json = json.dumps(data)
        row.fetched_at = datetime.utcnow()
        row.expires_at = expires
    else:
        db.add(ApiCache(
            cache_key=key,
            data_json=json.dumps(data),
            fetched_at=datetime.utcnow(),
            expires_at=expires,
        ))
    db.commit()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def search_movies(db: Session, query: str, page: int = 1) -> dict:
    """
    Search TMDb for movies matching *query*.
    Results are cached for SEARCH_CACHE_HOURS.
    """
    cache_key = f"search:{query.lower().strip()}:p{page}"
    cached = _get_cache(db, cache_key)
    if cached:
        return cached

    data = _get("/search/movie", {"query": query, "page": page, "include_adult": False})
    _set_cache(db, cache_key, data, ttl_hours=SEARCH_CACHE_HOURS)
    return data


def get_movie_detail(db: Session, tmdb_id: int) -> dict:
    """
    Fetch full movie detail from TMDb (or from the DB cache).
    Includes credits, videos (trailers), keywords.
    """
    cache_key = f"detail:{tmdb_id}"
    cached = _get_cache(db, cache_key)
    if cached:
        return cached

    data = _get(
        f"/movie/{tmdb_id}",
        {"append_to_response": "credits,videos,keywords,release_dates"},
    )
    _set_cache(db, cache_key, data, ttl_hours=CACHE_TTL_DAYS * 24)
    return data


def get_popular_movies(db: Session, page: int = 1) -> dict:
    """Fetch TMDb popular movies (cached for 6 hours)."""
    cache_key = f"popular:p{page}"
    cached = _get_cache(db, cache_key)
    if cached:
        return cached

    data = _get("/movie/popular", {"page": page})
    _set_cache(db, cache_key, data, ttl_hours=6)
    return data


def get_genres(db: Session) -> list[dict]:
    """Fetch the full TMDb genre list (cached for 7 days)."""
    cache_key = "genres:movie"
    cached = _get_cache(db, cache_key)
    if cached:
        return cached.get("genres", [])

    data = _get("/genre/movie/list")
    _set_cache(db, cache_key, data, ttl_hours=7 * 24)
    return data.get("genres", [])


# ---------------------------------------------------------------------------
# Poster download
# ---------------------------------------------------------------------------
def download_poster(tmdb_id: int, poster_path: str) -> str | None:
    """
    Download a poster image from TMDb CDN and save it locally.
    Returns the local file path (relative to MEDIA_DIR), or None on failure.
    """
    if not poster_path:
        return None

    posters_dir = Path(settings.MEDIA_DIR) / "posters"
    posters_dir.mkdir(parents=True, exist_ok=True)

    local_path = posters_dir / f"{tmdb_id}.jpg"

    # Already downloaded — skip
    if local_path.exists():
        return f"posters/{tmdb_id}.jpg"

    url = f"{IMAGE_BASE}{poster_path}"
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(url)
            resp.raise_for_status()
            local_path.write_bytes(resp.content)
        return f"posters/{tmdb_id}.jpg"
    except Exception as exc:  # noqa: BLE001
        print(f"[TMDb] Failed to download poster for {tmdb_id}: {exc}")
        return None


# ---------------------------------------------------------------------------
# Import helper — converts TMDb detail dict → local Movie row
# ---------------------------------------------------------------------------
def tmdb_detail_to_movie_dict(data: dict) -> dict:
    """
    Extract the fields we store in the `movies` table from a TMDb detail dict.
    Does NOT download the poster — call download_poster() separately.
    """
    return {
        "tmdb_id": data["id"],
        "imdb_id": data.get("imdb_id"),
        "title": data.get("title", ""),
        "original_title": data.get("original_title"),
        "overview": data.get("overview"),
        "release_date": data.get("release_date") or None,
        "runtime": data.get("runtime"),
        "poster_path": data.get("poster_path"),    # raw TMDb path, e.g. /abc.jpg
        "backdrop_path": data.get("backdrop_path"),
        "vote_average": data.get("vote_average"),
        "tagline": data.get("tagline"),
        "language": data.get("original_language"),
        "tmdb_data_json": json.dumps(data),
    }
