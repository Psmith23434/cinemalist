from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.movie import Movie
from app.models.movie_genre import MovieGenre
from app.schemas.movie import MovieRead
from app.services import tmdb as tmdb_service

router = APIRouter()


@router.get("/tmdb")
async def search_tmdb(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
):
    """
    Search TMDb for movies. Results are cached via the service layer (7-day TTL).
    Returns raw TMDb results so the frontend can display them before import.
    """
    return await tmdb_service.search_movies(q=q, page=page, db=db)


@router.post("/tmdb/import/{tmdb_id}", response_model=MovieRead, status_code=201)
async def import_from_tmdb(tmdb_id: int, db: AsyncSession = Depends(get_db)):
    """
    Import a TMDb movie into the local database.
    Delegates to the service layer which handles fetch, cache, upsert, and genres.
    Returns 409 if the movie is already imported.
    """
    existing = await db.execute(select(Movie).where(Movie.tmdb_id == tmdb_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Movie already imported")

    movie = await tmdb_service.import_movie(tmdb_id=tmdb_id, db=db)

    # Re-fetch with genres eagerly loaded for the response schema
    result = await db.execute(
        select(Movie)
        .where(Movie.id == movie.id)
        .options(selectinload(Movie.genres).selectinload(MovieGenre.genre))
    )
    return result.scalar_one()
