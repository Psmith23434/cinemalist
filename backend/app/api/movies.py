from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.core.database import get_db
from app.models.movie import Movie
from app.models.genre import Genre
from app.models.movie_genre import MovieGenre
from app.schemas.movie import MovieCreate, MovieUpdate, MovieRead, MovieSummary
from app.schemas.common import PaginatedResponse, MessageResponse

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[MovieSummary])
async def list_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    q: Optional[str] = Query(None, description="Filter by title substring"),
    db: AsyncSession = Depends(get_db),
):
    """Paginated list of all movies in the local database."""
    stmt = select(Movie)
    if q:
        stmt = stmt.where(Movie.title.ilike(f"%{q}%"))
    total_result = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = total_result.scalar_one()
    stmt = stmt.offset((page - 1) * per_page).limit(per_page).order_by(Movie.title)
    result = await db.execute(stmt)
    items = result.scalars().all()
    return {"total": total, "page": page, "per_page": per_page, "items": items}


@router.get("/{movie_id}", response_model=MovieRead)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Movie)
        .where(Movie.id == movie_id)
        .options(selectinload(Movie.genres).selectinload(MovieGenre.genre))
    )
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@router.post("/", response_model=MovieRead, status_code=201)
async def create_movie(body: MovieCreate, db: AsyncSession = Depends(get_db)):
    """Manually create a movie record (without TMDb)."""
    if body.tmdb_id:
        existing = await db.execute(select(Movie).where(Movie.tmdb_id == body.tmdb_id))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Movie with this TMDb ID already exists")
    movie = Movie(**body.model_dump())
    db.add(movie)
    await db.flush()
    await db.refresh(movie)
    return movie


@router.patch("/{movie_id}", response_model=MovieRead)
async def update_movie(
    movie_id: int, body: MovieUpdate, db: AsyncSession = Depends(get_db)  # Bug 6 fix: was MovieCreate
):
    movie = await db.get(Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(movie, field, value)
    await db.flush()
    await db.refresh(movie)
    return movie


@router.delete("/{movie_id}", response_model=MessageResponse)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await db.get(Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    await db.delete(movie)
    return {"message": f"Movie '{movie.title}' deleted", "ok": True}
