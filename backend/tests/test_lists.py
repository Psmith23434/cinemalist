"""
Tests for /api/lists/ — create, read, add items, delete.
"""
import pytest
from tests.conftest import create_test_movie


async def create_list(client, name: str = "My Favs") -> dict:
    r = await client.post("/api/lists/", json={"name": name, "description": "Test list"})
    assert r.status_code == 201, r.text
    return r.json()


@pytest.mark.asyncio
async def test_create_list(client):
    """POST /api/lists/ creates a new list."""
    data = await create_list(client, "Watchlist 2025")
    assert data["name"] == "Watchlist 2025"
    assert data["id"] > 0


@pytest.mark.asyncio
async def test_list_all_lists(client):
    """GET /api/lists/ returns all created lists."""
    await create_list(client, "List A")
    await create_list(client, "List B")
    r = await client.get("/api/lists/")
    assert r.status_code == 200
    assert len(r.json()) >= 2


@pytest.mark.asyncio
async def test_get_list_by_id(client):
    """GET /api/lists/{id} returns the correct list."""
    lst = await create_list(client, "Horror Classics")
    r = await client.get(f"/api/lists/{lst['id']}")
    assert r.status_code == 200
    assert r.json()["name"] == "Horror Classics"


@pytest.mark.asyncio
async def test_get_list_not_found(client):
    r = await client.get("/api/lists/9999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_add_item_to_list(client, db_session):
    """POST /api/lists/{id}/items adds a movie entry to a list."""
    from tests.conftest import create_test_movie
    movie = await create_test_movie(db_session)
    # Create entry first
    entry = (await client.post("/api/entries/", json={"movie_id": movie.id, "watched": False})).json()
    lst = await create_list(client)
    r = await client.post(f"/api/lists/{lst['id']}/items", json={"entry_id": entry["id"]})
    assert r.status_code == 201, r.text


@pytest.mark.asyncio
async def test_delete_list(client):
    """DELETE /api/lists/{id} soft-deletes a list."""
    lst = await create_list(client, "Temp List")
    r = await client.delete(f"/api/lists/{lst['id']}")
    assert r.status_code == 200
    assert r.json()["ok"] is True
    r2 = await client.get(f"/api/lists/{lst['id']}")
    assert r2.status_code == 404


@pytest.mark.asyncio
async def test_update_list(client):
    """PATCH /api/lists/{id} updates name and description."""
    lst = await create_list(client, "Old Name")
    r = await client.patch(f"/api/lists/{lst['id']}", json={"name": "New Name"})
    assert r.status_code == 200
    assert r.json()["name"] == "New Name"
