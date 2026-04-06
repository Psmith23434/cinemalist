from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timezone

from app.core.database import get_db
from app.models.entry import Entry
from app.models.watch_event import WatchEvent
from app.schemas.entry import EntryCreate, EntryUpdate, EntryRead
from app.schemas.watch_event import WatchEventCreate, WatchEventRead
from app.schemas.common import PaginatedResponse, MessageResponse

router = APIRouter()


def _entry_query():
    return (
        select(Entry)
        .where(Entry.deleted_at.is_(None))
        .options(
            selectinload(Entry.movie),
            selectinload(Entry.watch_events),
            selectinload(Entry.tags),
        )
    )


@router.get("/", response_model=PaginatedResponse[EntryRead])
async def list_entries(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    watched: Optional[bool] = None,
    is_favorite: Optional[bool] = None,
    is_watchlisted: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = _entry_query()
    if watched is not None:
        stmt = stmt.where(Entry.watched == watched)
    if is_favorite is not None:
        stmt = stmt.where(Entry.is_favorite == is_favorite)
    if is_watchlisted is not None:
        stmt = stmt.where(Entry.is_watchlisted == is_watchlisted)

    count_q = select(func.count(Entry.id)).where(Entry.deleted_at.is_(None))
    if watched is not None:
        count_q = count_q.where(Entry.watched == watched)
    if is_favorite is not None:
        count_q = count_q.where(Entry.is_favorite == is_favorite)
    if is_watchlisted is not None:
        count_q = count_q.where(Entry.is_watchlisted == is_watchlisted)

    total = await db.scalar(count_q)
    stmt = stmt.offset((page - 1) * per_page).limit(per_page).order_by(Entry.updated_at.desc())
    result = await db.execute(stmt)
    items = result.scalars().all()
    return {"total": total, "page": page, "per_page": per_page, "items": items}


@router.get("/{entry_id}", response_model=EntryRead)
async def get_entry(entry_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(_entry_query().where(Entry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.post("/", response_model=EntryRead, status_code=201)
async def create_entry(body: EntryCreate, db: AsyncSession = Depends(get_db)):
    """Create a personal entry for a movie. Movie must exist first."""
    from app.models.movie import Movie
    movie = await db.get(Movie, body.movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    existing = await db.execute(
        select(Entry).where(Entry.movie_id == body.movie_id, Entry.deleted_at.is_(None))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Entry for this movie already exists")
    entry = Entry(**body.model_dump())
    db.add(entry)
    await db.flush()
    if body.first_watched_at:
        db.add(WatchEvent(
            entry_id=entry.id,
            watched_at=body.first_watched_at,
        ))
    await db.commit()
    result = await db.execute(_entry_query().where(Entry.id == entry.id))
    return result.scalar_one()


@router.patch("/{entry_id}", response_model=EntryRead)
async def update_entry(
    entry_id: int, body: EntryUpdate, db: AsyncSession = Depends(get_db)
):
    from app.models.tag import Tag

    # Fetch with tags eagerly loaded — required so that assigning entry.tags
    # does NOT trigger a synchronous lazy load (which raises MissingGreenlet
    # in an async session). Without selectinload(Entry.tags) here, SQLAlchemy
    # attempts to load the existing collection synchronously before replacing it.
    result = await db.execute(
        select(Entry)
        .where(Entry.id == entry_id, Entry.deleted_at.is_(None))
        .options(selectinload(Entry.tags))
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    update_data = body.model_dump(exclude_unset=True)
    tag_ids = update_data.pop("tag_ids", None)

    for field, value in update_data.items():
        setattr(entry, field, value)
    entry.updated_at = datetime.now(timezone.utc)

    if tag_ids is not None:
        tags_result = await db.execute(select(Tag).where(Tag.id.in_(tag_ids)))
        entry.tags = list(tags_result.scalars().all())

    await db.flush()
    result = await db.execute(_entry_query().where(Entry.id == entry_id))
    return result.scalar_one()


@router.delete("/{entry_id}", response_model=MessageResponse)
async def delete_entry(entry_id: int, db: AsyncSession = Depends(get_db)):
    """Soft-delete — sets deleted_at instead of removing the row (needed for sync)."""
    entry = await db.get(Entry, entry_id)
    if not entry or entry.deleted_at:
        raise HTTPException(status_code=404, detail="Entry not found")
    entry.deleted_at = datetime.now(timezone.utc)
    return {"message": "Entry deleted", "ok": True}


# ── Watch Events ───────────────────────────────────────────────────────────────

@router.post("/{entry_id}/watches", response_model=WatchEventRead, status_code=201)
async def log_watch(
    entry_id: int, body: WatchEventCreate, db: AsyncSession = Depends(get_db)
):
    """Log a new watch (rewatch support)."""
    entry = await db.get(Entry, entry_id)
    if not entry or entry.deleted_at:
        raise HTTPException(status_code=404, detail="Entry not found")
    event = WatchEvent(
        entry_id=entry_id,
        watched_at=body.watched_at or datetime.now(timezone.utc),
        platform=body.platform,
        note=body.note,
    )
    db.add(event)
    if not entry.first_watched_at:
        entry.first_watched_at = event.watched_at
    entry.last_watched_at = event.watched_at
    entry.watched = True
    await db.flush()
    await db.refresh(event)
    return event


@router.get("/{entry_id}/watches", response_model=List[WatchEventRead])
async def list_watches(entry_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WatchEvent)
        .where(WatchEvent.entry_id == entry_id)
        .order_by(WatchEvent.watched_at.desc())
    )
    return result.scalars().all()


@router.delete("/{entry_id}/watches/{event_id}", response_model=MessageResponse)
async def delete_watch(
    entry_id: int, event_id: int, db: AsyncSession = Depends(get_db)
):
    event = await db.get(WatchEvent, event_id)
    if not event or event.entry_id != entry_id:
        raise HTTPException(status_code=404, detail="Watch event not found")
    await db.delete(event)
    await db.flush()

    entry = await db.get(Entry, entry_id)
    if entry:
        remaining = (
            await db.execute(
                select(WatchEvent)
                .where(WatchEvent.entry_id == entry_id)
                .order_by(WatchEvent.watched_at.desc())
            )
        ).scalars().all()
        if remaining:
            entry.last_watched_at  = remaining[0].watched_at
            entry.first_watched_at = remaining[-1].watched_at
        else:
            entry.last_watched_at  = None
            entry.first_watched_at = None
            entry.watched          = False

    return {"message": "Watch event deleted", "ok": True}
