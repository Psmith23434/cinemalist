from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel

from app.core.database import get_db
from app.models.entry import Entry
from app.schemas.entry import EntryRead

router = APIRouter()


class SyncPayload(BaseModel):
    """Push payload from Android (or another device)."""
    entries: List[dict] = []
    deleted_entry_uuids: List[str] = []


class SyncResponse(BaseModel):
    entries: List[EntryRead] = []
    server_time: datetime


class SyncPushResponse(BaseModel):
    message: str
    ok: bool
    created: int = 0
    updated: int = 0
    synced_at: datetime


async def _pull(since: Optional[datetime], db: AsyncSession) -> SyncResponse:
    """Shared pull logic — used by both '/' and '/pull' routes."""
    from sqlalchemy.orm import selectinload
    from app.models.watch_event import WatchEvent  # noqa: F401

    stmt = (
        select(Entry)
        .options(
            selectinload(Entry.movie),
            selectinload(Entry.watch_events),
            selectinload(Entry.tags),
        )
    )
    if since:
        stmt = stmt.where(Entry.updated_at > since)

    result = await db.execute(stmt)
    entries = result.scalars().all()
    return SyncResponse(entries=entries, server_time=datetime.now(timezone.utc))


@router.get("/", response_model=SyncResponse)
async def sync_root(
    since: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Pull alias on the root path — used by tests and simple clients."""
    return await _pull(since, db)


@router.get("/pull", response_model=SyncResponse)
async def sync_pull(
    since: Optional[datetime] = Query(
        None, description="ISO-8601 timestamp; returns records updated after this time"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Pull entries updated since `since`.
    Pass the `server_time` from the previous pull/push response as `since=`
    on the next call to receive only the delta.
    """
    return await _pull(since, db)


@router.post("/push", response_model=SyncPushResponse)
async def sync_push(payload: SyncPayload, db: AsyncSession = Depends(get_db)):
    """
    Receive changes from Android. Last-write-wins on updated_at.
    New entries (no matching UUID on server) are CREATED.
    Existing entries are updated if the incoming timestamp is newer.
    """
    from app.models.movie import Movie

    created_count = 0
    updated_count = 0

    for entry_data in payload.entries:
        uuid = entry_data.get("uuid")

        # ── Try to find an existing entry by UUID ──────────────────────────
        existing_entry = None
        if uuid:
            res = await db.execute(select(Entry).where(Entry.uuid == uuid))
            existing_entry = res.scalar_one_or_none()

        if existing_entry:
            # Last-write-wins: only apply if incoming is strictly newer
            incoming_updated = entry_data.get("updated_at")
            if incoming_updated and existing_entry.updated_at:
                try:
                    incoming_dt = datetime.fromisoformat(
                        str(incoming_updated).replace("Z", "+00:00")
                    )
                    server_dt = (
                        existing_entry.updated_at.replace(tzinfo=timezone.utc)
                        if existing_entry.updated_at.tzinfo is None
                        else existing_entry.updated_at
                    )
                    if incoming_dt <= server_dt:
                        continue
                except (ValueError, AttributeError):
                    continue

            for field in [
                "rating", "notes", "review",
                "is_favorite", "is_watchlisted", "watched", "deleted_at",
            ]:
                if field in entry_data:
                    setattr(existing_entry, field, entry_data[field])
            updated_count += 1

        else:
            # ── Create new entry from push payload ─────────────────────────
            movie_id = entry_data.get("movie_id")
            if not movie_id:
                continue
            movie = await db.get(Movie, movie_id)
            if not movie:
                continue

            new_entry = Entry(
                movie_id=movie_id,
                watched=entry_data.get("watched", False),
                rating=entry_data.get("rating"),
                notes=entry_data.get("notes"),
                review=entry_data.get("review"),
                is_favorite=entry_data.get("is_favorite", False),
                is_watchlisted=entry_data.get("is_watchlisted", False),
            )
            if uuid:
                new_entry.uuid = uuid
            db.add(new_entry)
            created_count += 1

    # Handle deletions sent from Android
    for uuid in payload.deleted_entry_uuids:
        result = await db.execute(select(Entry).where(Entry.uuid == uuid))
        entry = result.scalar_one_or_none()
        if entry and not entry.deleted_at:
            entry.deleted_at = datetime.now(timezone.utc)

    synced_at = datetime.now(timezone.utc)
    return SyncPushResponse(
        message=f"Sync complete — {len(payload.entries)} entries processed",
        ok=True,
        created=created_count,
        updated=updated_count,
        synced_at=synced_at,
    )
