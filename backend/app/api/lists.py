from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.models.list import MovieList
from app.models.list_item import ListItem
from app.models.entry import Entry
from app.models.movie import Movie
from app.schemas.list import MovieListCreate, MovieListUpdate, MovieListRead, MovieListDetail
from app.schemas.common import MessageResponse

router = APIRouter()


@router.get("/", response_model=List[MovieListRead])
async def list_lists(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieList)
        .where(MovieList.deleted_at.is_(None))
        .order_by(MovieList.name)
    )
    return result.scalars().all()


@router.post("/", response_model=MovieListRead, status_code=201)
async def create_list(body: MovieListCreate, db: AsyncSession = Depends(get_db)):
    ml = MovieList(**body.model_dump())
    db.add(ml)
    await db.flush()
    await db.refresh(ml)
    return ml


@router.get("/{list_id}", response_model=MovieListDetail)
async def get_list(list_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieList)
        .where(MovieList.id == list_id, MovieList.deleted_at.is_(None))
        .options(
            selectinload(MovieList.items)
            .selectinload(ListItem.entry)
            .selectinload(Entry.movie)  # Bug 5: was missing — caused MissingGreenlet on serialization
        )
    )
    ml = result.scalar_one_or_none()
    if not ml:
        raise HTTPException(status_code=404, detail="List not found")
    return ml


@router.patch("/{list_id}", response_model=MovieListRead)
async def update_list(
    list_id: int, body: MovieListUpdate, db: AsyncSession = Depends(get_db)
):
    ml = await db.get(MovieList, list_id)
    if not ml or ml.deleted_at:
        raise HTTPException(status_code=404, detail="List not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(ml, field, value)
    ml.updated_at = datetime.utcnow()
    await db.flush()
    await db.refresh(ml)
    return ml


@router.delete("/{list_id}", response_model=MessageResponse)
async def delete_list(list_id: int, db: AsyncSession = Depends(get_db)):
    ml = await db.get(MovieList, list_id)
    if not ml or ml.deleted_at:
        raise HTTPException(status_code=404, detail="List not found")
    ml.deleted_at = datetime.utcnow()
    return {"message": f"List '{ml.name}' deleted", "ok": True}


@router.post("/{list_id}/entries/{entry_id}", response_model=MessageResponse)
async def add_entry_to_list(
    list_id: int, entry_id: int, db: AsyncSession = Depends(get_db)
):
    ml = await db.get(MovieList, list_id)
    if not ml or ml.deleted_at:
        raise HTTPException(status_code=404, detail="List not found")
    entry = await db.get(Entry, entry_id)
    if not entry or entry.deleted_at:
        raise HTTPException(status_code=404, detail="Entry not found")
    existing = await db.execute(
        select(ListItem).where(ListItem.list_id == list_id, ListItem.entry_id == entry_id)
    )
    if existing.scalar_one_or_none():
        return {"message": "Entry already in list", "ok": True}
    count_result = await db.execute(
        select(ListItem).where(ListItem.list_id == list_id)
    )
    position = len(count_result.scalars().all())
    db.add(ListItem(list_id=list_id, entry_id=entry_id, position=position))
    return {"message": "Entry added to list", "ok": True}


@router.delete("/{list_id}/entries/{entry_id}", response_model=MessageResponse)
async def remove_entry_from_list(
    list_id: int, entry_id: int, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ListItem).where(ListItem.list_id == list_id, ListItem.entry_id == entry_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Entry not in list")
    await db.delete(item)
    return {"message": "Entry removed from list", "ok": True}
