"""Tests for /api/sync/ pull and push endpoints."""
import pytest
from datetime import datetime, timezone
from tests.conftest import create_test_movie

# Correct URLs:
#   GET  /api/sync/pull  (not /api/sync/)
#   POST /api/sync/push  (correct)


@pytest.mark.asyncio
async def test_sync_pull_empty(client):
    """Pull with no entries returns empty entries list."""
    r = await client.get("/api/sync/pull?since=2020-01-01T00:00:00")
    assert r.status_code == 200
    data = r.json()
    assert "entries" in data
    assert isinstance(data["entries"], list)
    assert len(data["entries"]) == 0


@pytest.mark.asyncio
async def test_sync_pull_returns_new_entries(client, db_session):
    """Pull returns entries created after the 'since' timestamp."""
    movie = await create_test_movie(db_session)
    await client.post("/api/entries/", json={"movie_id": movie.id, "watched": True})
    # Pull with a far-past timestamp — should include the new entry
    r = await client.get("/api/sync/pull?since=2000-01-01T00:00:00")
    assert r.status_code == 200
    data = r.json()
    assert "entries" in data
    assert len(data["entries"]) >= 1


@pytest.mark.asyncio
async def test_sync_pull_excludes_old_entries(client, db_session):
    """Pull with a far-future timestamp returns zero entries."""
    movie = await create_test_movie(db_session)
    await client.post("/api/entries/", json={"movie_id": movie.id, "watched": True})
    r = await client.get("/api/sync/pull?since=2099-01-01T00:00:00")
    assert r.status_code == 200
    assert len(r.json()["entries"]) == 0


@pytest.mark.asyncio
async def test_sync_push_creates_entry(client, db_session):
    """Push a payload from the Android client — server acknowledges.

    The push endpoint (POST /api/sync/push) processes the entries list and
    returns: {message: str, ok: bool, synced_at: str}
    It does NOT return 'created'/'updated' counts — it processes by UUID match.
    We verify the response shape and that `ok` is True.
    """
    movie = await create_test_movie(db_session)
    now = datetime.now(timezone.utc).isoformat()
    r = await client.post("/api/sync/push", json={"entries": [{
        "movie_id": movie.id,
        "watched": True,
        "rating": 7.5,
        "notes": "Synced from phone",
        "is_favorite": False,
        "is_watchlisted": False,
        "updated_at": now,
    }]})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert "message" in data
    assert "synced_at" in data
