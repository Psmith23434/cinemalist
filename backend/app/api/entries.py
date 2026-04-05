"""
Entries router — /api/entries

Endpoints
---------
GET    /api/entries/                           List entries (filterable)
GET    /api/entries/{id}                       Single entry
POST   /api/entries/                           Create entry
PATCH  /api/entries/{id}                       Update entry
DELETE /api/entries/{id}                       Soft-delete entry
POST   /api/entries/{id}/watch-events          Log a watch/rewatch
DELETE /api/entries/{id}/watch-events/{we_id}  Remove a watch event
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
from typing import Optional

from app.core.database import get_db
from app.models.entry import Entry
from app.models.movie import Movie
from app.models.movie_genre import MovieGenre
from app.models.tag import Tag
from app.models.entry_tag import EntryTag
from app.models.watch_event import WatchEvent
from app.schemas.entry import EntryCreate, EntryUpdate, EntryOut, WatchEventCreate, WatchEventOut

router = APIRouter()


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_or_create_tags(db: AsyncSession, names: list[str]) -> list[Tag]:
    tags: list[Tag] = []
    for name in names:
        name = name.strip().lower()
        if not name:
            continue
        result = await db.execute(select(Tag).where(Tag.name == name))
        tag = result.scalar_one_or_none()
        if not tag:
            tag = Tag(name=name)
            db.add(tag)
            await db.flush()
        tags.append(tag)
    return tags


ENTRY_LOAD_OPTIONS = [
    selectinload(Entry.movie).selectinload(Movie.genres),
    selectinload(Entry.watch_events),
    selectinload(Entry.tags).selectinload(EntryTag.tag),
]


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("/", response_model=list[EntryOut])
async def list_entries(
    watched:        Optional[bool]  = None,
    is_favorite:    Optional[bool]  = None,
    is_watchlisted: Optional[bool]  = None,
    tag:            Optional[str]   = Query(None, description="Filter by tag name"),
    genre_id:       Optional[int]   = Query(None, description="Filter by genre ID"),
    rating_min:     Optional[float] = Query(None, ge=0.5, le=10.0, description="Minimum rating"),
    rating_max:     Optional[float] = Query(None, ge=0.5, le=10.0, description="Maximum rating"),
    year:           Optional[int]   = Query(None, description="Filter by movie release year"),
    sort_by: str = Query(
        "updated_at",
        enum=["updated_at", "rating", "first_watched_at", "title"],
    ),
    order: str = Query("desc", enum=["asc", "desc"]),
    skip:  int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Entry)
        .options(*ENTRY_LOAD_OPTIONS)
        .where(Entry.deleted_at.is_(None))
    )

    # ── Boolean filters ───────────────────────────────────────────────────────
    if watched is not None:
        stmt = stmt.where(Entry.watched == watched)
    if is_favorite is not None:
        stmt = stmt.where(Entry.is_favorite == is_favorite)
    if is_watchlisted is not None:
        stmt = stmt.where(Entry.is_watchlisted == is_watchlisted)

    # ── Rating range ──────────────────────────────────────────────────────────
    if rating_min is not None:
        stmt = stmt.where(Entry.rating >= rating_min)
    if rating_max is not None:
        stmt = stmt.where(Entry.rating <= rating_max)

    # ── Genre filter (join through movie) ─────────────────────────────────────
    if genre_id is not None:
        stmt = (
            stmt
            .join(Movie, Movie.id == Entry.movie_id)
            .join(MovieGenre, MovieGenre.movie_id == Movie.id)
            .where(MovieGenre.genre_id == genre_id)
        )

    # ── Release year filter ───────────────────────────────────────────────────
    if year is not None:
        if genre_id is None:          # avoid double-join
            stmt = stmt.join(Movie, Movie.id == Entry.movie_id)
        stmt = stmt.where(Movie.year == year)

    # ── Tag filter ────────────────────────────────────────────────────────────
    if tag is not None:
        tag_norm = tag.strip().lower()
        stmt = (
            stmt
            .join(EntryTag, EntryTag.entry_id == Entry.id)
            .join(Tag, Tag.id == EntryTag.tag_id)
            .where(Tag.name == tag_norm)
        )

    # ── Sort ──────────────────────────────────────────────────────────────────
    if sort_by == "title":
        # Sort by movie title — need a join unless already joined
        sort_col = Movie.title
        if genre_id is None and year is None:
            stmt = stmt.join(Movie, Movie.id == Entry.movie_id)
    else:
        sort_col = getattr(Entry, sort_by, Entry.updated_at)

    stmt = stmt.order_by(sort_col.desc() if order == "desc" else sort_col.asc())
    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute(stmt)
    return result.scalars().unique().all()


# ── Get single ────────────────────────────────────────────────────────────────

@router.get("/{entry_id}", response_model=EntryOut)
async def get_entry(entry_id: int, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Entry)
        .options(*ENTRY_LOAD_OPTIONS)
        .where(Entry.id == entry_id, Entry.deleted_at.is_(None))
    )
    result = await db.execute(stmt)
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


# ── Create ────────────────────────────────────────────────────────────────────

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

    # Reload with all relationships so EntryOut can serialise correctly
    await db.refresh(entry)
    result = await db.execute(
        select(Entry).options(*ENTRY_LOAD_OPTIONS).where(Entry.id == entry.id)
    )
    return result.scalar_one()


# ── Update ────────────────────────────────────────────────────────────────────

@router.patch("/{entry_id}", response_model=EntryOut)
async def update_entry(entry_id: int, data: EntryUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Entry)
        .options(*ENTRY_LOAD_OPTIONS)
        .where(Entry.id == entry_id, Entry.deleted_at.is_(None))
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    update_data = data.model_dump(exclude_unset=True, exclude={"tag_names"})
    for field, value in update_data.items():
        setattr(entry, field, value)

    if data.tag_names is not None:
        await db.execute(
            delete(EntryTag).where(EntryTag.entry_id == entry_id)
        )
        tags = await _get_or_create_tags(db, data.tag_names)
        for tag in tags:
            db.add(EntryTag(entry_id=entry.id, tag_id=tag.id))

    await db.flush()

    result = await db.execute(
        select(Entry).options(*ENTRY_LOAD_OPTIONS).where(Entry.id == entry_id)
    )
    return result.scalar_one()


# ── Delete (soft) ─────────────────────────────────────────────────────────────

@router.delete("/{entry_id}", status_code=204)
async def delete_entry(entry_id: int, db: AsyncSession = Depends(get_db)):
    """Soft delete — preserves sync history."""
    result = await db.execute(select(Entry).where(Entry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    entry.deleted_at = datetime.now(timezone.utc)


# ── Watch Events ──────────────────────────────────────────────────────────────

@router.post("/{entry_id}/watch-events", response_model=WatchEventOut, status_code=201)
async def log_watch_event(
    entry_id: int,
    data: WatchEventCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Log a new watch / rewatch for this entry.
    Also updates `entry.last_watched_at` and sets `entry.watched = True`.
    If `entry.first_watched_at` is not set and a date is provided, it is
    set here too.
    """
    result = await db.execute(
        select(Entry).where(Entry.id == entry_id, Entry.deleted_at.is_(None))
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    event = WatchEvent(
        entry_id=entry_id,
        watched_at=data.watched_at,
        platform=data.platform,
        note=data.note,
    )
    db.add(event)

    # Keep entry dates in sync
    entry.watched = True
    if data.watched_at:
        if not entry.first_watched_at:
            entry.first_watched_at = data.watched_at
        if not entry.last_watched_at or data.watched_at > entry.last_watched_at:
            entry.last_watched_at = data.watched_at

    await db.flush()
    await db.refresh(event)
    return event


@router.delete("/{entry_id}/watch-events/{watch_event_id}", status_code=204)
async def delete_watch_event(
    entry_id: int,
    watch_event_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Remove a specific watch event. The entry itself is NOT deleted."""
    result = await db.execute(
        select(WatchEvent).where(
            WatchEvent.id == watch_event_id,
            WatchEvent.entry_id == entry_id,
        )
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Watch event not found")
    await db.delete(event)
