from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import httpx
import json
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.config import settings
from app.models.movie import Movie
from app.models.tmdb_cache import TmdbCache
from app.schemas.movie import MovieRead, MovieCreate

router = APIRouter()

TMDB_HEADERS = {"Authorization": f"Bearer {settings.TMDB_API_KEY}"}


async def _fetch_tmdb(path: str, params: dict = {}) -> dict:
    """Raw TMDb API call."""
    if not settings.TMDB_API_KEY:
        raise HTTPException(status_code=503, detail="TMDb API key not configured")
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{settings.TMDB_BASE_URL}{path}",
            headers={"Authorization": f"Bearer {settings.TMDB_API_KEY}"},
            params=params,
            timeout=10.0,
        )
        r.raise_for_status()
        return r.json()


@router.get("/tmdb")
async def search_tmdb(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
):
    """
    Search TMDb for movies. Results are lightly cached (1 hour TTL).
    Returns raw TMDb results so the frontend can display them before import.
    """
    cache_key = f"search:{q.lower().strip()}:p{page}"
    cached = await db.execute(select(TmdbCache).where(TmdbCache.cache_key == cache_key))
    row = cached.scalar_one_or_none()
    if row and row.expires_at and row.expires_at > datetime.utcnow():
        return json.loads(row.data_json)

    data = await _fetch_tmdb("/search/movie", {"query": q, "page": page})

    # Upsert cache
    expires = datetime.utcnow() + timedelta(hours=1)
    if row:
        row.data_json = json.dumps(data)
        row.expires_at = expires
        row.fetched_at = datetime.utcnow()
    else:
        db.add(TmdbCache(cache_key=cache_key, data_json=json.dumps(data), expires_at=expires))

    return data


@router.post("/tmdb/import/{tmdb_id}", response_model=MovieRead, status_code=201)
async def import_from_tmdb(tmdb_id: int, db: AsyncSession = Depends(get_db)):
    """
    Import a TMDb movie into the local database.
    Fetches full details, saves to `movies` table, downloads poster.
    """
    # Check if already imported
    existing = await db.execute(select(Movie).where(Movie.tmdb_id == tmdb_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Movie already imported")

    data = await _fetch_tmdb(f"/movie/{tmdb_id}", {"append_to_response": "credits"})

    # Extract director from credits
    director = None
    cast_top5 = None
    credits = data.get("credits", {})
    crew = credits.get("crew", [])
    for person in crew:
        if person.get("job") == "Director":
            director = person.get("name")
            break
    cast = credits.get("cast", [])[:5]
    if cast:
        cast_top5 = json.dumps([c["name"] for c in cast])

    # Parse year from release_date
    release_date = data.get("release_date", "")
    year = int(release_date[:4]) if release_date and len(release_date) >= 4 else None

    movie = Movie(
        tmdb_id=tmdb_id,
        imdb_id=data.get("imdb_id"),
        title=data.get("title", "Unknown"),
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
        cast_top5=cast_top5,
    )
    db.add(movie)
    await db.flush()

    # Save genres
    from app.models.genre import Genre
    from app.models.movie_genre import MovieGenre
    for g in data.get("genres", []):
        genre_result = await db.execute(select(Genre).where(Genre.tmdb_id == g["id"]))
        genre = genre_result.scalar_one_or_none()
        if not genre:
            genre = Genre(tmdb_id=g["id"], name=g["name"])
            db.add(genre)
            await db.flush()
        db.add(MovieGenre(movie_id=movie.id, genre_id=genre.id))

    # Cache full TMDb response (30-day TTL)
    cache_key = f"movie:{tmdb_id}"
    expires = datetime.utcnow() + timedelta(days=30)
    db.add(TmdbCache(cache_key=cache_key, data_json=json.dumps(data), expires_at=expires))

    await db.flush()
    from sqlalchemy.orm import selectinload
    from app.models.movie_genre import MovieGenre as MG
    result = await db.execute(
        select(Movie).where(Movie.id == movie.id)
        .options(selectinload(Movie.genres).selectinload(MG.genre))
    )
    return result.scalar_one()
