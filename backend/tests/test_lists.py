"""Tests for /api/lists/ — CRUD and list-item management."""
import pytest
from tests.conftest import create_test_movie


async def create_list(client, name: str = "My List") -> dict:
    """Helper: create a list and return its JSON."""
    r = await client.post("/api/lists/", json={"name": name})
    assert r.status_code == 201, r.text
    return r.json()


@pytest.mark.asyncio
async def test_create_list(client):
    """POST /api/lists/ creates a new list."""
    r = await client.post("/api/lists/", json={"name": "Favourites"})
    assert r.status_code == 201
    assert r.json()["name"] == "Favourites"


@pytest.mark.asyncio
async def test_list_all_lists(client):
    """GET /api/lists/ returns all lists."""
    await create_list(client, "List One")
    await create_list(client, "List Two")
    r = await client.get("/api/lists/")
    assert r.status_code == 200
    assert len(r.json()) >= 2


@pytest.mark.asyncio
async def test_get_list_by_id(client):
    """GET /api/lists/{id} returns the correct list."""
    lst = await create_list(client, "Detail List")
    r = await client.get(f"/api/lists/{lst['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == lst["id"]


@pytest.mark.asyncio
async def test_get_list_not_found(client):
    """GET /api/lists/99999 returns 404."""
    r = await client.get("/api/lists/99999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_add_item_to_list(client, db_session):
    """POST /api/lists/{id}/entries/{entry_id} adds a movie entry to a list.

    The endpoint is: POST /api/lists/{list_id}/entries/{entry_id}
    (entry_id is a path param, NOT a JSON body field)
    """
    movie = await create_test_movie(db_session)
    entry = (await client.post("/api/entries/", json={"movie_id": movie.id, "watched": False})).json()
    lst = await create_list(client)
    # Correct URL: entry_id is a path segment, not a body
    r = await client.post(f"/api/lists/{lst['id']}/entries/{entry['id']}")
    assert r.status_code == 200, r.text
    assert r.json()["ok"] is True


@pytest.mark.asyncio
async def test_delete_list(client):
    """DELETE /api/lists/{id} soft-deletes the list."""
    lst = await create_list(client, "To Delete")
    r = await client.delete(f"/api/lists/{lst['id']}")
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert (await client.get(f"/api/lists/{lst['id']}")).status_code == 404


@pytest.mark.asyncio
async def test_update_list(client):
    """PATCH /api/lists/{id} updates the list name."""
    lst = await create_list(client, "Old Name")
    r = await client.patch(f"/api/lists/{lst['id']}", json={"name": "New Name"})
    assert r.status_code == 200
    assert r.json()["name"] == "New Name"
