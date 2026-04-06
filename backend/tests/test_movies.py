"""
Tests for GET /api/movies/ and GET /api/movies/{id}
"""
import pytest
from tests.conftest import create_test_movie


@pytest.mark.asyncio
async def test_list_movies_empty(client):
    """Library starts empty."""
    r = await client.get("/api/movies/")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_list_movies_returns_seeded(client, db_session):
    """A seeded movie appears in the list."""
    await create_test_movie(db_session, tmdb_id=550, title="Fight Club")
    r = await client.get("/api/movies/")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Fight Club"


@pytest.mark.asyncio
async def test_get_movie_by_id(client, db_session):
    """GET /api/movies/{id} returns the correct movie."""
    movie = await create_test_movie(db_session, tmdb_id=278, title="The Shawshank Redemption")
    r = await client.get(f"/api/movies/{movie.id}")
    assert r.status_code == 200
    assert r.json()["title"] == "The Shawshank Redemption"
    assert r.json()["tmdb_id"] == 278


@pytest.mark.asyncio
async def test_get_movie_not_found(client):
    """GET /api/movies/9999 returns 404."""
    r = await client.get("/api/movies/9999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_list_movies_pagination(client, db_session):
    """Pagination: per_page=1 returns only 1 item but total reflects all."""
    await create_test_movie(db_session, tmdb_id=1, title="Movie A")
    await create_test_movie(db_session, tmdb_id=2, title="Movie B")
    r = await client.get("/api/movies/?per_page=1&page=1")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 2
    assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_search_movies_by_title(client, db_session):
    """GET /api/movies/?q= filters by title."""
    await create_test_movie(db_session, tmdb_id=1, title="Inception")
    await create_test_movie(db_session, tmdb_id=2, title="Interstellar")
    r = await client.get("/api/movies/?q=Inception")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Inception"
