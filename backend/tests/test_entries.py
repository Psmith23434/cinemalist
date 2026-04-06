"""
Tests for /api/entries/ — create, read, update, delete, watch events.
"""
import pytest
from tests.conftest import create_test_movie


# ── helpers ───────────────────────────────────────────────────────────────────
async def seed_entry(client, movie_id: int, rating: float = 8.0) -> dict:
    """POST /api/entries/ and return the response JSON."""
    r = await client.post("/api/entries/", json={
        "movie_id": movie_id,
        "rating": rating,
        "notes": "Great film",
        "watched": True,
        "is_favorite": False,
        "is_watchlisted": False,
    })
    assert r.status_code == 201, r.text
    return r.json()


# ── create ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_entry(client, db_session):
    """Successfully create an entry for an existing movie."""
    movie = await create_test_movie(db_session)
    entry = await seed_entry(client, movie.id)
    assert entry["movie_id"] == movie.id
    assert entry["rating"] == 8.0
    assert entry["notes"] == "Great film"


@pytest.mark.asyncio
async def test_create_entry_movie_not_found(client):
    """Creating an entry for a non-existent movie returns 404."""
    r = await client.post("/api/entries/", json={"movie_id": 9999, "watched": False})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_create_entry_duplicate_returns_409(client, db_session):
    """Creating two entries for the same movie returns 409."""
    movie = await create_test_movie(db_session)
    await seed_entry(client, movie.id)
    r = await client.post("/api/entries/", json={"movie_id": movie.id, "watched": False})
    assert r.status_code == 409


# ── read ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_entries_empty(client):
    r = await client.get("/api/entries/")
    assert r.status_code == 200
    assert r.json()["total"] == 0


@pytest.mark.asyncio
async def test_get_entry_by_id(client, db_session):
    movie = await create_test_movie(db_session)
    entry = await seed_entry(client, movie.id)
    r = await client.get(f"/api/entries/{entry['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == entry["id"]


@pytest.mark.asyncio
async def test_get_entry_not_found(client):
    r = await client.get("/api/entries/9999")
    assert r.status_code == 404


# ── update ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_entry_rating(client, db_session):
    """PATCH /api/entries/{id} updates rating correctly."""
    movie = await create_test_movie(db_session)
    entry = await seed_entry(client, movie.id, rating=7.0)
    r = await client.patch(f"/api/entries/{entry['id']}", json={"rating": 9.5})
    assert r.status_code == 200
    assert r.json()["rating"] == 9.5


@pytest.mark.asyncio
async def test_update_entry_favorite(client, db_session):
    """PATCH sets is_favorite correctly."""
    movie = await create_test_movie(db_session)
    entry = await seed_entry(client, movie.id)
    r = await client.patch(f"/api/entries/{entry['id']}", json={"is_favorite": True})
    assert r.status_code == 200
    assert r.json()["is_favorite"] is True


@pytest.mark.asyncio
async def test_update_entry_notes(client, db_session):
    movie = await create_test_movie(db_session)
    entry = await seed_entry(client, movie.id)
    r = await client.patch(f"/api/entries/{entry['id']}", json={"notes": "Updated note"})
    assert r.status_code == 200
    assert r.json()["notes"] == "Updated note"


# ── delete ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_entry(client, db_session):
    """DELETE soft-deletes: entry disappears from list but 404 on re-fetch."""
    movie = await create_test_movie(db_session)
    entry = await seed_entry(client, movie.id)
    r = await client.delete(f"/api/entries/{entry['id']}")
    assert r.status_code == 200
    assert r.json()["ok"] is True
    r2 = await client.get(f"/api/entries/{entry['id']}")
    assert r2.status_code == 404


@pytest.mark.asyncio
async def test_delete_entry_not_found(client):
    r = await client.delete("/api/entries/9999")
    assert r.status_code == 404


# ── filters ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_filter_favorites(client, db_session):
    """is_favorite=true filter returns only favourites."""
    m1 = await create_test_movie(db_session, tmdb_id=1, title="A")
    m2 = await create_test_movie(db_session, tmdb_id=2, title="B")
    e1 = await seed_entry(client, m1.id)
    await seed_entry(client, m2.id)
    await client.patch(f"/api/entries/{e1['id']}", json={"is_favorite": True})
    r = await client.get("/api/entries/?is_favorite=true")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["is_favorite"] is True


@pytest.mark.asyncio
async def test_filter_watchlist(client, db_session):
    """is_watchlisted=true filter works correctly."""
    m1 = await create_test_movie(db_session, tmdb_id=3, title="C")
    m2 = await create_test_movie(db_session, tmdb_id=4, title="D")
    e1 = await seed_entry(client, m1.id)
    await seed_entry(client, m2.id)
    await client.patch(f"/api/entries/{e1['id']}", json={"is_watchlisted": True})
    r = await client.get("/api/entries/?is_watchlisted=true")
    assert r.status_code == 200
    assert r.json()["total"] == 1


# ── watch events ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_log_watch_event(client, db_session):
    """POST /api/entries/{id}/watches logs a watch event."""
    movie = await create_test_movie(db_session)
    entry = await seed_entry(client, movie.id)
    r = await client.post(f"/api/entries/{entry['id']}/watches", json={
        "watched_at": "2025-12-25T20:00:00",
        "platform": "Netflix",
        "note": "Christmas watch",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["platform"] == "Netflix"
    assert data["note"] == "Christmas watch"


@pytest.mark.asyncio
async def test_list_watch_events(client, db_session):
    """GET /api/entries/{id}/watches returns all logged watches."""
    movie = await create_test_movie(db_session)
    entry = await seed_entry(client, movie.id)
    await client.post(f"/api/entries/{entry['id']}/watches", json={"watched_at": "2024-01-01T10:00:00"})
    await client.post(f"/api/entries/{entry['id']}/watches", json={"watched_at": "2025-06-15T10:00:00"})
    r = await client.get(f"/api/entries/{entry['id']}/watches")
    assert r.status_code == 200
    assert len(r.json()) == 2


@pytest.mark.asyncio
async def test_delete_watch_event(client, db_session):
    """DELETE /api/entries/{id}/watches/{wid} removes a watch event."""
    movie = await create_test_movie(db_session)
    entry = await seed_entry(client, movie.id)
    w = (await client.post(f"/api/entries/{entry['id']}/watches", json={"watched_at": "2025-01-01T00:00:00"})).json()
    r = await client.delete(f"/api/entries/{entry['id']}/watches/{w['id']}")
    assert r.status_code == 200
    remaining = (await client.get(f"/api/entries/{entry['id']}/watches")).json()
    assert len(remaining) == 0
