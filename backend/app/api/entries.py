from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
from app.core.database import get_db
from app.models.entry import Entry
from app.models.tag import Tag
from app.models.entry_tag import EntryTag
from app.schemas.entry import EntryCreate, EntryUpdate, EntryOut
from typing import Optional

router = APIRouter()


async def _get_or_create_tags(db: AsyncSession, names: list[str]) -> list[Tag]:
    tags = []
    for name in names:
        name = name.strip().lower()
        result = await db.execute(select(Tag).where(Tag.name == name))
        tag = result.scalar_one_or_none()
        if not tag:
            tag = Tag(name=name)
            db.add(tag)
            await db.flush()
        tags.append(tag)
    return tags


@router.get("/", response_model=list[EntryOut])
async def list_entries(
    watched: Optional[bool] = None,
    is_favorite: Optional[bool] = None,
    is_watchlisted: Optional[bool] = None,
    tag: Optional[str] = None,
    sort_by: str = Query("updated_at", enum=["updated_at", "rating", "first_watched_at", "title"]),
    order: str = Query("desc", enum=["asc", "desc"]),
    skip: int = 0,
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Entry)
        .options(
            selectinload(Entry.movie),
            selectinload(Entry.watch_events),
            selectinload(Entry.tags).selectinload(EntryTag.tag),
        )
        .where(Entry.deleted_at.is_(None))
    )
    if watched is not None:
        stmt = stmt.where(Entry.watched == watched)
    if is_favorite is not None:
        stmt = stmt.where(Entry.is_favorite == is_favorite)
    if is_watchlisted is not None:
        stmt = stmt.where(Entry.is_watchlisted == is_watchlisted)

    sort_col = getattr(Entry, sort_by, Entry.updated_at)
    stmt = stmt.order_by(sort_col.desc() if order == "desc" else sort_col.asc())
    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{entry_id}", response_model=EntryOut)
async def get_entry(entry_id: int, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Entry)
        .options(
            selectinload(Entry.movie),
            selectinload(Entry.watch_events),
            selectinload(Entry.tags).selectinload(EntryTag.tag),
        )
        .where(Entry.id == entry_id, Entry.deleted_at.is_(None))
    )
    result = await db.execute(stmt)
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.post("/", response_model=EntryOut, status_code=201)
async def create_entry(data: EntryCreate, db: AsyncSession = Depends(get_db)):
    # Prevent duplicate entries for the same movie
    existing = await db.execute(
        select(Entry).where(Entry.movie_id == data.movie_id, Entry.deleted_at.is_(None))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Entry for this movie already exists")

    tag_names = data.tag_names
    entry_data = data.model_dump(exclude={"tag_names"})
    entry = Entry(**entry_data)
    db.add(entry)
    await db.flush()

    tags = await _get_or_create_tags(db, tag_names)
    for tag in tags:
        db.add(EntryTag(entry_id=entry.id, tag_id=tag.id))

    await db.flush()
    return entry


@router.patch("/{entry_id}", response_model=EntryOut)
async def update_entry(entry_id: int, data: EntryUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Entry)
        .options(selectinload(Entry.tags).selectinload(EntryTag.tag))
        .where(Entry.id == entry_id, Entry.deleted_at.is_(None))
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    update_data = data.model_dump(exclude_unset=True, exclude={"tag_names"})
    for field, value in update_data.items():
        setattr(entry, field, value)

    if data.tag_names is not None:
        # Replace all tags
        await db.execute(
            EntryTag.__table__.delete().where(EntryTag.entry_id == entry_id)
        )
        tags = await _get_or_create_tags(db, data.tag_names)
        for tag in tags:
            db.add(EntryTag(entry_id=entry.id, tag_id=tag.id))

    await db.flush()
    return entry


@router.delete("/{entry_id}", status_code=204)
async def delete_entry(entry_id: int, db: AsyncSession = Depends(get_db)):
    """Soft delete — preserves sync history."""
    result = await db.execute(select(Entry).where(Entry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    entry.deleted_at = datetime.now(timezone.utc)
