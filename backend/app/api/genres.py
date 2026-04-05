from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.genre import Genre
from app.schemas.movie import GenreOut

router = APIRouter()


@router.get("/", response_model=list[GenreOut])
async def list_genres(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Genre).order_by(Genre.name))
    return result.scalars().all()
