"""
Tests for /api/sync/ — pull and push.
"""
import pytest
from datetime import datetime, timezone
from tests.conftest import create_test_movie


@pytest.mark.asyncio
async def test_sync_pull_empty(client):
    """Pull with no entries returns empty list."""
    r = await client.get("/api/sync/?since=2020-01-01T00:00:00")
    assert r.status_code == 200
    data = r.json()
    assert "entries" in data
    assert isinstance(data["entries"], list)


@pytest.mark.asyncio
async def test_sync_pull_returns_new_entries(client, db_session):
    """Pull returns entries created after the 'since' timestamp."""
    movie = await create_test_movie(db_session)
    await client.post("/api/entries/", json={"movie_id": movie.id, "watched": True})
    # Pull with a past timestamp — should include the new entry
    r = await client.get("/api/sync/?since=2000-01-01T00:00:00")
    assert r.status_code == 200
    assert len(r.json()["entries"]) >= 1


@pytest.mark.asyncio
async def test_sync_pull_excludes_old_entries(client, db_session):
    """Pull with a future timestamp returns zero entries."""
    movie = await create_test_movie(db_session)
    await client.post("/api/entries/", json={"movie_id": movie.id, "watched": True})
    r = await client.get("/api/sync/?since=2099-01-01T00:00:00")
    assert r.status_code == 200
    assert len(r.json()["entries"]) == 0


@pytest.mark.asyncio
async def test_sync_push_creates_entry(client, db_session):
    """Push a new entry from the Android client — it should be created."""
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
    assert "created" in data or "updated" in data or "results" in data
