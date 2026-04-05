from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.models.genre import Genre
from app.models.movie_genre import MovieGenre
from app.schemas.genre import GenreRead

router = APIRouter()


@router.get("/", response_model=List[GenreRead])
async def list_genres(db: AsyncSession = Depends(get_db)):
    """Return all genres in the database."""
    result = await db.execute(select(Genre).order_by(Genre.name))
    return result.scalars().all()


@router.get("/{genre_id}", response_model=GenreRead)
async def get_genre(genre_id: int, db: AsyncSession = Depends(get_db)):
    genre = await db.get(Genre, genre_id)
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")
    return genre
