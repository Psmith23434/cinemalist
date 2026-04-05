"""Movie endpoints — local DB movies + TMDb import."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import json

from app.core.database import get_db
from app.models.movie import Movie
from app.models.genre import Genre
from app.models.movie_genre import MovieGenre
from app.schemas.movie import MovieCreate, MovieOut
from app.services.tmdb import tmdb

router = APIRouter()


# ---------------------------------------------------------------------------
# List / Get
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[MovieOut], summary="List local movies")
async def list_movies(
    q: Optional[str] = Query(None, description="Filter by title (partial match)"),
    year: Optional[int] = Query(None, description="Filter by release year"),
    genre: Optional[str] = Query(None, description="Filter by genre name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Movie)
    if q:
        stmt = stmt.where(Movie.title.ilike(f"%{q}%"))
    if year:
        stmt = stmt.where(Movie.year == year)
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{movie_id}", response_model=MovieOut, summary="Get a local movie by ID")
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Movie).where(Movie.id == movie_id))
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


# ---------------------------------------------------------------------------
# Manual create
# ---------------------------------------------------------------------------

@router.post("/", response_model=MovieOut, status_code=201, summary="Create movie manually")
async def create_movie(data: MovieCreate, db: AsyncSession = Depends(get_db)):
    if data.tmdb_id:
        existing = await db.execute(select(Movie).where(Movie.tmdb_id == data.tmdb_id))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Movie with this TMDb ID already exists")
    movie = Movie(**data.model_dump())
    db.add(movie)
    await db.flush()
    return movie


# ---------------------------------------------------------------------------
# TMDb import  <-- KEY Phase 3 endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/import/{tmdb_id}",
    response_model=MovieOut,
    status_code=201,
    summary="Import a movie from TMDb into the local DB",
)
async def import_from_tmdb(
    tmdb_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Fetch full metadata from TMDb and save it as a local Movie row.

    - If the movie already exists locally (same ``tmdb_id``) the existing
      record is returned with HTTP 200 instead of 201 — safe to call
      multiple times.
    - Genres are upserted into the ``genres`` table and linked via
      ``movie_genres``.
    - ``director`` and ``cast_top5`` (JSON array) are denormalised onto
      the Movie row for fast reads.
    """
    # --- Idempotency: return existing if already imported ---
    existing_result = await db.execute(select(Movie).where(Movie.tmdb_id == tmdb_id))
    existing = existing_result.scalar_one_or_none()
    if existing:
        return existing

    # --- Fetch from TMDb (uses cache) ---
    data = await tmdb.get_movie_detail(tmdb_id=tmdb_id, db=db)

    release = data.get("release_date") or ""
    year = int(release[:4]) if len(release) >= 4 else None

    movie = Movie(
        tmdb_id=data["id"],
        imdb_id=data.get("imdb_id"),
        title=data.get("title", ""),
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
        director=data.get("director"),
        cast_top5=json.dumps(data.get("cast_top5", [])),
    )
    db.add(movie)
    await db.flush()  # assigns movie.id

    # --- Upsert genres + link ---
    for genre_data in data.get("genres", []):
        genre_result = await db.execute(
            select(Genre).where(Genre.tmdb_id == genre_data["id"])
        )
        genre = genre_result.scalar_one_or_none()
        if not genre:
            genre = Genre(tmdb_id=genre_data["id"], name=genre_data["name"])
            db.add(genre)
            await db.flush()

        # Link movie ↔ genre (avoid duplicates)
        link_result = await db.execute(
            select(MovieGenre).where(
                MovieGenre.movie_id == movie.id,
                MovieGenre.genre_id == genre.id,
            )
        )
        if not link_result.scalar_one_or_none():
            db.add(MovieGenre(movie_id=movie.id, genre_id=genre.id))

    await db.flush()
    return movie


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

@router.delete("/{movie_id}", status_code=204, summary="Delete a local movie")
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Movie).where(Movie.id == movie_id))
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    await db.delete(movie)
