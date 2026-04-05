"""
Movies router — /api/movies

Endpoints
---------
GET    /api/movies/               List / search local movie catalogue
GET    /api/movies/{id}           Get single movie by local ID
POST   /api/movies/               Manually create a movie record
PATCH  /api/movies/{id}           Update movie metadata
DELETE /api/movies/{id}           Remove a movie (cascades to entries)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Literal, Optional

from app.core.database import get_db
from app.models.genre import Genre
from app.models.movie import Movie
from app.models.movie_genre import MovieGenre
from app.schemas.movie import MovieCreate, MovieOut

router = APIRouter()


# ── List / search ─────────────────────────────────────────────────────────────

@router.get("/", response_model=list[MovieOut], summary="List local movies")
async def list_movies(
    q:         Optional[str]                        = Query(None, description="Title search (case-insensitive)"),
    year:      Optional[int]                        = Query(None, description="Filter by release year"),
    genre_id:  Optional[int]                        = Query(None, description="Filter by genre ID"),
    order_by:  Literal["title", "year", "created_at"] = Query("title"),
    direction: Literal["asc", "desc"]               = Query("asc"),
    skip:      int                                  = Query(0, ge=0),
    limit:     int                                  = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Movie).options(selectinload(Movie.genres))

    if q:
        stmt = stmt.where(Movie.title.ilike(f"%{q}%"))
    if year:
        stmt = stmt.where(Movie.year == year)
    if genre_id:
        stmt = stmt.join(MovieGenre, MovieGenre.movie_id == Movie.id).where(
            MovieGenre.genre_id == genre_id
        )

    sort_col = getattr(Movie, order_by)
    stmt = stmt.order_by(asc(sort_col) if direction == "asc" else desc(sort_col))
    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute(stmt)
    movies = result.scalars().unique().all()
    return movies


# ── Get single ────────────────────────────────────────────────────────────────

@router.get("/{movie_id}", response_model=MovieOut, summary="Get movie by ID")
async def get_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Movie)
        .options(selectinload(Movie.genres))
        .where(Movie.id == movie_id)
    )
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


# ── Create (manual) ───────────────────────────────────────────────────────────

@router.post("/", response_model=MovieOut, status_code=201, summary="Manually add a movie")
async def create_movie(
    data: MovieCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Manually create a movie record without fetching from TMDb.
    Useful for films not in the TMDb catalogue.
    """
    if data.tmdb_id:
        clash = (await db.execute(
            select(Movie).where(Movie.tmdb_id == data.tmdb_id)
        )).scalar_one_or_none()
        if clash:
            raise HTTPException(status_code=409, detail="Movie with this TMDb ID already exists")

    movie = Movie(**data.model_dump(exclude={"tmdb_genre_ids"}, exclude_none=False))
    db.add(movie)
    await db.flush()

    # Link genres if tmdb_genre_ids provided
    for gid in getattr(data, "tmdb_genre_ids", None) or []:
        genre = (await db.execute(select(Genre).where(Genre.tmdb_id == gid))).scalar_one_or_none()
        if genre:
            db.add(MovieGenre(movie_id=movie.id, genre_id=genre.id))

    await db.flush()
    await db.refresh(movie, attribute_names=["genres"])
    return movie


# ── Update ────────────────────────────────────────────────────────────────────

@router.patch("/{movie_id}", response_model=MovieOut, summary="Update movie metadata")
async def update_movie(
    movie_id: int,
    data: MovieCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Movie).options(selectinload(Movie.genres)).where(Movie.id == movie_id)
    )
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    update_data = data.model_dump(exclude_unset=True, exclude={"tmdb_genre_ids"})
    for k, v in update_data.items():
        setattr(movie, k, v)

    await db.flush()
    await db.refresh(movie, attribute_names=["genres"])
    return movie


# ── Delete ────────────────────────────────────────────────────────────────────

@router.delete("/{movie_id}", status_code=204, summary="Delete a movie")
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Movie).where(Movie.id == movie_id))
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    await db.delete(movie)
