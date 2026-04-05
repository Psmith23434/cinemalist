from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List

from app.core.database import get_db
from app.models.tag import Tag
from app.models.entry_tag import EntryTag
from app.schemas.tag import TagRead, TagCreate
from app.schemas.common import MessageResponse

router = APIRouter()


@router.get("/", response_model=List[TagRead])
async def list_tags(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tag).order_by(Tag.name))
    return result.scalars().all()


@router.post("/", response_model=TagRead, status_code=201)
async def create_tag(body: TagCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Tag).where(Tag.name == body.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Tag already exists")
    tag = Tag(name=body.name)
    db.add(tag)
    await db.flush()
    await db.refresh(tag)
    return tag


@router.delete("/{tag_id}", response_model=MessageResponse)
async def delete_tag(tag_id: int, db: AsyncSession = Depends(get_db)):
    tag = await db.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    await db.delete(tag)
    return {"message": f"Tag '{tag.name}' deleted", "ok": True}


@router.post("/entry/{entry_id}/{tag_id}", response_model=MessageResponse)
async def add_tag_to_entry(
    entry_id: int, tag_id: int, db: AsyncSession = Depends(get_db)
):
    """Attach a tag to an entry."""
    from app.models.entry import Entry
    entry = await db.get(Entry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    tag = await db.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    existing = await db.execute(
        select(EntryTag).where(EntryTag.entry_id == entry_id, EntryTag.tag_id == tag_id)
    )
    if existing.scalar_one_or_none():
        return {"message": "Tag already on entry", "ok": True}
    db.add(EntryTag(entry_id=entry_id, tag_id=tag_id))
    return {"message": "Tag added", "ok": True}


@router.delete("/entry/{entry_id}/{tag_id}", response_model=MessageResponse)
async def remove_tag_from_entry(
    entry_id: int, tag_id: int, db: AsyncSession = Depends(get_db)
):
    await db.execute(
        delete(EntryTag).where(EntryTag.entry_id == entry_id, EntryTag.tag_id == tag_id)
    )
    return {"message": "Tag removed", "ok": True}
