from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.core.database import get_db
from app.models.movie import Movie
from app.models.genre import Genre
from app.models.movie_genre import MovieGenre
from app.schemas.movie import MovieCreate, MovieOut
from typing import Optional

router = APIRouter()


@router.get("/", response_model=list[MovieOut])
async def list_movies(
    q: Optional[str] = Query(None, description="Search by title"),
    year: Optional[int] = None,
    genre: Optional[str] = None,
    skip: int = 0,
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


@router.get("/{movie_id}", response_model=MovieOut)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Movie).where(Movie.id == movie_id))
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@router.post("/", response_model=MovieOut, status_code=201)
async def create_movie(data: MovieCreate, db: AsyncSession = Depends(get_db)):
    # Check for duplicate TMDb ID
    if data.tmdb_id:
        existing = await db.execute(select(Movie).where(Movie.tmdb_id == data.tmdb_id))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Movie with this TMDb ID already exists")
    movie = Movie(**data.model_dump())
    db.add(movie)
    await db.flush()
    return movie


@router.delete("/{movie_id}", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Movie).where(Movie.id == movie_id))
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    await db.delete(movie)
