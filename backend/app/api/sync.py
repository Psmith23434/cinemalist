from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from app.core.database import get_db
from app.models.entry import Entry
from app.models.sync_log import SyncLog
from app.schemas.entry import EntryOut
from sqlalchemy.orm import selectinload
from app.models.entry_tag import EntryTag

router = APIRouter()


@router.get("/delta")
async def delta_sync(
    device_id: str = Query(...),
    since: datetime = Query(None, description="ISO8601 timestamp — get all entries updated after this"),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns all entries modified since the given timestamp.
    Android app calls this on startup to pull changes from the server.
    """
    stmt = (
        select(Entry)
        .options(
            selectinload(Entry.movie),
            selectinload(Entry.watch_events),
            selectinload(Entry.tags).selectinload(EntryTag.tag),
        )
    )
    if since:
        stmt = stmt.where(Entry.updated_at > since)

    result = await db.execute(stmt)
    entries = result.scalars().all()

    # Update sync log
    log = (await db.execute(select(SyncLog).where(SyncLog.device_id == device_id))).scalar_one_or_none()
    if log:
        log.last_synced_at = datetime.now(timezone.utc)
    else:
        db.add(SyncLog(device_id=device_id, last_synced_at=datetime.now(timezone.utc)))
    await db.flush()

    return {
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "count": len(entries),
        "entries": [EntryOut.model_validate(e) for e in entries],
    }
