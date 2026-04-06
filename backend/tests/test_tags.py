"""
Tests for /api/tags/ — create, list, assign to entry, delete.
"""
import pytest
from tests.conftest import create_test_movie


async def create_tag(client, name: str = "Thriller") -> dict:
    r = await client.post("/api/tags/", json={"name": name, "color": "#ff0000"})
    assert r.status_code == 201, r.text
    return r.json()


@pytest.mark.asyncio
async def test_create_tag(client):
    data = await create_tag(client, "Sci-Fi")
    assert data["name"] == "Sci-Fi"
    assert data["id"] > 0


@pytest.mark.asyncio
async def test_list_tags(client):
    await create_tag(client, "Drama")
    await create_tag(client, "Comedy")
    r = await client.get("/api/tags/")
    assert r.status_code == 200
    assert len(r.json()) >= 2


@pytest.mark.asyncio
async def test_duplicate_tag_returns_409(client):
    """Creating two tags with the same name returns 409."""
    await create_tag(client, "Action")
    r = await client.post("/api/tags/", json={"name": "Action", "color": "#00ff00"})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_delete_tag(client):
    tag = await create_tag(client, "Delete Me")
    r = await client.delete(f"/api/tags/{tag['id']}")
    assert r.status_code == 200
    assert r.json()["ok"] is True


@pytest.mark.asyncio
async def test_assign_tag_to_entry(client, db_session):
    """PATCH /api/entries/{id} with tag_ids assigns tags."""
    movie = await create_test_movie(db_session)
    entry = (await client.post("/api/entries/", json={"movie_id": movie.id, "watched": False})).json()
    tag = await create_tag(client, "Mystery")
    r = await client.patch(f"/api/entries/{entry['id']}", json={"tag_ids": [tag["id"]]})
    assert r.status_code == 200
    tags_in_response = r.json().get("tags", [])
    assert any(t["id"] == tag["id"] for t in tags_in_response)
