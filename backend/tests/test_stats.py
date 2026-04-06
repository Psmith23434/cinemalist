"""
Tests for GET /api/stats/
"""
import pytest
from tests.conftest import create_test_movie


@pytest.mark.asyncio
async def test_stats_empty(client):
    """Stats on empty library return zero totals."""
    r = await client.get("/api/stats/")
    assert r.status_code == 200
    data = r.json()
    assert data["total_movies"] == 0
    assert data["total_watched"] == 0


@pytest.mark.asyncio
async def test_stats_counts_entries(client, db_session):
    """Stats reflect correct watched count."""
    m1 = await create_test_movie(db_session, tmdb_id=1, title="A")
    m2 = await create_test_movie(db_session, tmdb_id=2, title="B")
    # Add two entries, only one marked watched
    await client.post("/api/entries/", json={"movie_id": m1.id, "watched": True, "rating": 8.0})
    await client.post("/api/entries/", json={"movie_id": m2.id, "watched": False})
    r = await client.get("/api/stats/")
    assert r.status_code == 200
    data = r.json()
    assert data["total_movies"] == 2
    assert data["total_watched"] == 1


@pytest.mark.asyncio
async def test_stats_average_rating(client, db_session):
    """Average rating is calculated correctly."""
    m1 = await create_test_movie(db_session, tmdb_id=10, title="X")
    m2 = await create_test_movie(db_session, tmdb_id=11, title="Y")
    await client.post("/api/entries/", json={"movie_id": m1.id, "watched": True, "rating": 6.0})
    await client.post("/api/entries/", json={"movie_id": m2.id, "watched": True, "rating": 10.0})
    r = await client.get("/api/stats/")
    assert r.status_code == 200
    avg = r.json()["average_rating"]
    assert avg is not None
    assert abs(avg - 8.0) < 0.01


@pytest.mark.asyncio
async def test_stats_has_expected_keys(client):
    """Stats response always includes required top-level keys."""
    r = await client.get("/api/stats/")
    assert r.status_code == 200
    data = r.json()
    for key in ("total_movies", "total_watched", "average_rating",
                "top_genres", "by_year", "total_watchlisted"):
        assert key in data, f"Missing key: {key}"
