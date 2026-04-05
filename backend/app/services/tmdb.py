"""
TMDb service layer.

All TMDb HTTP calls go through here. Results are cached in the
`tmdb_cache` table for TMDB_CACHE_TTL_DAYS days to avoid hammering
the API on repeated lookups.

Public helpers
--------------
  search_movies(q, page, db)          → raw TMDb /search/movie response
  get_movie_details(tmdb_id, db)      → raw TMDb /movie/{id}?append_to_response=credits
  import_movie(tmdb_id, db)           → upsert Movie + Genre rows, return Movie ORM object
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.genre import Genre
from app.models.movie import Movie
from app.models.movie_genre import MovieGenre
from app.models.tmdb_cache import TmdbCache

CACHE_TTL_DAYS = 7


# ── Low-level cached HTTP helper ──────────────────────────────────────────────

async def _tmdb_get(path: str, params: dict[str, Any], db: AsyncSession) -> dict:
    """GET a TMDb endpoint, returning cached JSON when fresh."""
    cache_key = path + "::" + json.dumps(params, sort_keys=True)

    row: TmdbCache | None = (
        await db.execute(select(TmdbCache).where(TmdbCache.cache_key == cache_key))
    ).scalar_one_or_none()

    if row and row.expires_at and row.expires_at > datetime.now(timezone.utc):
        return json.loads(row.data_json)

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{settings.TMDB_BASE_URL}{path}",
            params={"api_key": settings.TMDB_API_KEY, **params},
        )

    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Movie not found on TMDb")
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"TMDb returned {resp.status_code}")

    data: dict = resp.json()
    expires_at = datetime.now(timezone.utc) + timedelta(days=CACHE_TTL_DAYS)

    if row:
        row.data_json = json.dumps(data)
        row.expires_at = expires_at
        row.fetched_at = datetime.now(timezone.utc)
    else:
        db.add(
            TmdbCache(
                cache_key=cache_key,
                data_json=json.dumps(data),
                expires_at=expires_at,
            )
        )
    await db.flush()
    return data


# ── Public search / detail helpers ───────────────────────────────────────────

async def search_movies(q: str, page: int, db: AsyncSession) -> dict:
    """Search TMDb by title. Returns the raw TMDb response dict."""
    return await _tmdb_get(
        "/search/movie",
        {"query": q, "page": page, "include_adult": "false"},
        db,
    )


async def get_movie_details(tmdb_id: int, db: AsyncSession) -> dict:
    """Fetch full movie details + credits from TMDb."""
    return await _tmdb_get(
        f"/movie/{tmdb_id}",
        {"append_to_response": "credits"},
        db,
    )


# ── Import helper ─────────────────────────────────────────────────────────────

async def import_movie(tmdb_id: int, db: AsyncSession) -> Movie:
    """
    Fetch full TMDb details for *tmdb_id* and upsert into the local DB.

    Steps
    -----
    1. Check whether a Movie with this tmdb_id already exists.
    2. Fetch /movie/{tmdb_id}?append_to_response=credits from TMDb (cached).
    3. Parse director and top-5 cast from the credits payload.
    4. Upsert the Movie row.
    5. Upsert Genre rows and link via MovieGenre join table.
    6. Return the Movie ORM object (not yet committed — caller must commit).
    """
    data = await get_movie_details(tmdb_id, db)

    # ── Parse director ──────────────────────────────────────────────────────
    director: str | None = None
    cast_top5: list[str] = []
    if credits := data.get("credits"):
        crew = credits.get("crew", [])
        directors = [p["name"] for p in crew if p.get("job") == "Director"]
        director = ", ".join(directors) if directors else None
        cast_top5 = [
            p["name"] for p in sorted(
                credits.get("cast", []),
                key=lambda x: x.get("order", 999),
            )[:5]
        ]

    # ── Release year ────────────────────────────────────────────────────────
    year: int | None = None
    if release_date := data.get("release_date"):
        try:
            year = int(release_date[:4])
        except (ValueError, TypeError):
            pass

    # ── Upsert Movie ────────────────────────────────────────────────────────
    existing: Movie | None = (
        await db.execute(select(Movie).where(Movie.tmdb_id == tmdb_id))
    ).scalar_one_or_none()

    movie_fields = dict(
        tmdb_id=tmdb_id,
        imdb_id=data.get("imdb_id"),
        title=data.get("title") or data.get("original_title", "Unknown"),
        original_title=data.get("original_title"),
        year=year,
        overview=data.get("overview"),
        tagline=data.get("tagline"),
        runtime=data.get("runtime"),
        language=data.get("original_language"),
        status=data.get("status"),
        tmdb_rating=data.get("vote_average"),
        tmdb_vote_count=data.get("vote_count"),
        poster_path=data.get("poster_path"),
        backdrop_path=data.get("backdrop_path"),
        director=director,
        cast_top5=json.dumps(cast_top5) if cast_top5 else None,
    )

    if existing:
        for k, v in movie_fields.items():
            setattr(existing, k, v)
        movie = existing
    else:
        movie = Movie(**movie_fields)
        db.add(movie)

    await db.flush()  # populate movie.id

    # ── Upsert Genres + join rows ────────────────────────────────────────────
    tmdb_genres: list[dict] = data.get("genres", [])

    # Fetch or create each Genre
    genre_objs: list[Genre] = []
    for g in tmdb_genres:
        genre_row: Genre | None = (
            await db.execute(select(Genre).where(Genre.tmdb_id == g["id"]))
        ).scalar_one_or_none()
        if not genre_row:
            genre_row = Genre(name=g["name"], tmdb_id=g["id"])
            db.add(genre_row)
            await db.flush()
        elif genre_row.name != g["name"]:
            genre_row.name = g["name"]
        genre_objs.append(genre_row)

    # Remove stale join rows, add new ones
    existing_links = (
        await db.execute(
            select(MovieGenre).where(MovieGenre.movie_id == movie.id)
        )
    ).scalars().all()
    existing_genre_ids = {mg.genre_id for mg in existing_links}
    new_genre_ids = {g.id for g in genre_objs}

    for mg in existing_links:
        if mg.genre_id not in new_genre_ids:
            await db.delete(mg)

    for genre in genre_objs:
        if genre.id not in existing_genre_ids:
            db.add(MovieGenre(movie_id=movie.id, genre_id=genre.id))

    await db.flush()
    return movie
