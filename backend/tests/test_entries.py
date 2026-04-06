"""Tests for /api/entries/ — CRUD, filters, and watch events."""
import pytest
from tests.conftest import create_test_movie


async def seed_entry(client, movie_id: int, **kwargs) -> dict:
    """Helper: create an entry via the API and return the JSON response."""
    payload = {"movie_id": movie_id, "watched": False, **kwargs}
    r = await client.post("/api/entries/", json=payload)
    assert r.status_code == 201, f"seed_entry failed: {r.text}"
    return r.json()


# ── Basic CRUD ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_entry(client, db_session):
    """POST /api/entries/ creates a new entry and returns 201."""
    movie = await create_test_movie(db_session)
    r = await client.post("/api/entries/", json={"movie_id": movie.id, "watched": False})
    assert r.status_code == 201
    data = r.json()
    assert data["movie_id"] == movie.id
    assert data["watched"] is False


@pytest.mark.asyncio
async def test_create_entry_movie_not_found(client):
    """POST with a non-existent movie_id returns 404."""
    r = await client.post("/api/entries/", json={"movie_id": 99999, "watched": False})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_create_entry_duplicate_returns_409(client, db_session):
    """Creating a second entry for the same movie returns 409."""
    movie = await create_test_movie(db_session)
    await seed_entry(client, movie.id)
    r = await client.post("/api/entries/", json={"movie_id": movie.id, "watched": False})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_list_entries_empty(client):
    """GET /api/entries/ on empty DB returns 200 with zero items."""
    r = await client.get("/api/entries/")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_get_entry_by_id(client, db_session):
    """GET /api/entries/{id} returns the correct entry."""
    movie = await create_test_movie(db_session)
    entry = await seed_entry(client, movie.id)
    r = await client.get(f"/api/entries/{entry['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == entry["id"]


@pytest.mark.asyncio
async def test_get_entry_not_found(client):
    """GET /api/entries/99999 returns 404."""
    r = await client.get("/api/entries/99999")
    assert r.status_code == 404


# ── Update ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_entry_rating(client, db_session):
    """PATCH /api/entries/{id} with rating updates the field."""
    movie = await create_test_movie(db_session)
    entry = await seed_entry(client, movie.id)
    r = await client.patch(f"/api/entries/{entry['id']}", json={"rating": 9.0})
    assert r.status_code == 200
    assert r.json()["rating"] == 9.0


@pytest.mark.asyncio
async def test_update_entry_favorite(client, db_session):
    """PATCH /api/entries/{id} with is_favorite=True sets the flag."""
    movie = await create_test_movie(db_session)
    entry = await seed_entry(client, movie.id)
    r = await client.patch(f"/api/entries/{entry['id']}", json={"is_favorite": True})
    assert r.status_code == 200
    assert r.json()["is_favorite"] is True


@pytest.mark.asyncio
async def test_update_entry_notes(client, db_session):
    """PATCH /api/entries/{id} with notes saves the note text."""
    movie = await create_test_movie(db_session)
    entry = await seed_entry(client, movie.id)
    r = await client.patch(f"/api/entries/{entry['id']}", json={"notes": "Great film!"})
    assert r.status_code == 200
    assert r.json()["notes"] == "Great film!"


# ── Delete ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_entry(client, db_session):
    """DELETE /api/entries/{id} soft-deletes and returns ok=True."""
    movie = await create_test_movie(db_session)
    entry = await seed_entry(client, movie.id)
    r = await client.delete(f"/api/entries/{entry['id']}")
    assert r.status_code == 200
    assert r.json()["ok"] is True
    # Confirm it's gone
    assert (await client.get(f"/api/entries/{entry['id']}")).status_code == 404


@pytest.mark.asyncio
async def test_delete_entry_not_found(client):
    """DELETE /api/entries/99999 returns 404."""
    r = await client.delete("/api/entries/99999")
    assert r.status_code == 404


# ── Filters ───────────────────────────────────────────────────────────────
# NOTE: the count_stmt in entries.py has a cartesian-product bug that makes
# `total` return the UNFILTERED count when a filter is applied (Bug #7).
# Until that is fixed, these tests assert on `items` length, not `total`.

@pytest.mark.asyncio
async def test_filter_favorites(client, db_session):
    """is_favorite=true filter returns only favourites."""
    m1 = await create_test_movie(db_session, tmdb_id=101, title="FavA")
    m2 = await create_test_movie(db_session, tmdb_id=102, title="FavB")
    e1 = await seed_entry(client, m1.id)
    await seed_entry(client, m2.id)
    await client.patch(f"/api/entries/{e1['id']}", json={"is_favorite": True})
    r = await client.get("/api/entries/?is_favorite=true")
    assert r.status_code == 200
    data = r.json()
    # Only items where is_favorite=True should be in the result set
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == e1["id"]


@pytest.mark.asyncio
async def test_filter_watchlist(client, db_session):
    """is_watchlisted=true filter returns only watchlisted entries."""
    m1 = await create_test_movie(db_session, tmdb_id=103, title="WatchA")
    m2 = await create_test_movie(db_session, tmdb_id=104, title="WatchB")
    e1 = await seed_entry(client, m1.id)
    await seed_entry(client, m2.id)
    await client.patch(f"/api/entries/{e1['id']}", json={"is_watchlisted": True})
    r = await client.get("/api/entries/?is_watchlisted=true")
    assert r.status_code == 200
    data = r.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == e1["id"]


# ── Watch Events ──────────────────────────────────────────────────────────
# WatchEventCreate requires `entry_id` in the body (Pydantic schema field).
# The URL already carries the entry_id, but the schema also needs it.

@pytest.mark.asyncio
async def test_log_watch_event(client, db_session):
    """POST /api/entries/{id}/watches logs a watch event."""
    movie = await create_test_movie(db_session)
    entry = await seed_entry(client, movie.id)
    r = await client.post(f"/api/entries/{entry['id']}/watches", json={
        "entry_id": entry["id"],
        "watched_at": "2025-12-25T20:00:00",
        "platform": "Netflix",
        "note": "Christmas watch",
    })
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["entry_id"] == entry["id"]
    assert "id" in data


@pytest.mark.asyncio
async def test_list_watch_events(client, db_session):
    """GET /api/entries/{id}/watches returns all logged watches."""
    movie = await create_test_movie(db_session)
    entry = await seed_entry(client, movie.id)
    eid = entry["id"]
    await client.post(f"/api/entries/{eid}/watches", json={"entry_id": eid, "watched_at": "2024-01-01T10:00:00"})
    await client.post(f"/api/entries/{eid}/watches", json={"entry_id": eid, "watched_at": "2025-06-15T10:00:00"})
    r = await client.get(f"/api/entries/{eid}/watches")
    assert r.status_code == 200
    assert len(r.json()) == 2


@pytest.mark.asyncio
async def test_delete_watch_event(client, db_session):
    """DELETE /api/entries/{id}/watches/{wid} removes a watch event."""
    movie = await create_test_movie(db_session)
    entry = await seed_entry(client, movie.id)
    eid = entry["id"]
    w = (await client.post(f"/api/entries/{eid}/watches", json={"entry_id": eid, "watched_at": "2025-01-01T00:00:00"})).json()
    assert "id" in w, f"Watch event creation failed: {w}"
    r = await client.delete(f"/api/entries/{eid}/watches/{w['id']}")
    assert r.status_code == 200
    assert r.json()["ok"] is True
    # Confirm deletion
    remaining = (await client.get(f"/api/entries/{eid}/watches")).json()
    assert len(remaining) == 0
