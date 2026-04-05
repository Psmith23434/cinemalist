from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.models.entry import Entry
from app.models.watch_event import WatchEvent
from app.schemas.entry import EntryRead
from app.schemas.watch_event import WatchEventRead
from app.schemas.common import MessageResponse

router = APIRouter()


class SyncPayload(BaseModel):
    """Push payload from Android (or another device)."""
    entries: List[dict] = []
    deleted_entry_uuids: List[str] = []


class SyncResponse(BaseModel):
    entries: List[EntryRead] = []
    server_time: datetime


@router.get("/pull", response_model=SyncResponse)
async def sync_pull(
    since: Optional[datetime] = Query(None, description="ISO-8601 timestamp; returns records updated after this time"),
    db: AsyncSession = Depends(get_db),
):
    """
    Pull all entries (and soft-deleted records) updated since `since`.
    Used by Android to get the latest changes from the server.
    """
    from sqlalchemy.orm import selectinload
    from app.models.watch_event import WatchEvent
    from app.models.entry_tag import EntryTag

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
    return SyncResponse(entries=entries, server_time=datetime.utcnow())


@router.post("/push", response_model=MessageResponse)
async def sync_push(payload: SyncPayload, db: AsyncSession = Depends(get_db)):
    """
    Receive changes from Android. Last-write-wins on updated_at.
    """
    for entry_data in payload.entries:
        uuid = entry_data.get("uuid")
        if not uuid:
            continue
        existing = await db.execute(select(Entry).where(Entry.uuid == uuid))
        existing_entry = existing.scalar_one_or_none()
        incoming_updated = entry_data.get("updated_at")
        if existing_entry:
            # Last write wins
            if incoming_updated and existing_entry.updated_at:
                if incoming_updated <= existing_entry.updated_at.isoformat():
                    continue  # Server version is newer — skip
            for field in ["rating", "notes", "review", "is_favorite", "is_watchlisted", "watched", "deleted_at"]:
                if field in entry_data:
                    setattr(existing_entry, field, entry_data[field])
        # Note: we do not create new movies via sync push in Phase 2;
        # full sync creation will be added in Phase 8 (Android app).

    # Process soft-deletes
    for uuid in payload.deleted_entry_uuids:
        result = await db.execute(select(Entry).where(Entry.uuid == uuid))
        entry = result.scalar_one_or_none()
        if entry and not entry.deleted_at:
            entry.deleted_at = datetime.utcnow()

    return {"message": f"Sync complete — {len(payload.entries)} entries processed", "ok": True}
