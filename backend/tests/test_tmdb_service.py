"""
Unit tests for the TMDb service layer.
These tests mock the HTTP calls — no real API key needed.
"""
from unittest.mock import MagicMock, patch
import json
import pytest

from app.services.tmdb import (
    tmdb_detail_to_movie_dict,
    _get_cache,
    _set_cache,
)


SAMPLE_DETAIL = {
    "id": 550,
    "title": "Fight Club",
    "original_title": "Fight Club",
    "overview": "A ticking-time-bomb insomniac...",
    "release_date": "1999-10-15",
    "runtime": 139,
    "vote_average": 8.4,
    "genres": [{"id": 18, "name": "Drama"}],
    "poster_path": "/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
    "backdrop_path": "/fCayJrkfRaCRCTh8GqN30f8oyQF.jpg",
    "imdb_id": "tt0137523",
    "original_language": "en",
    "tagline": "Mischief. Mayhem. Soap.",
}


def test_tmdb_detail_to_movie_dict():
    result = tmdb_detail_to_movie_dict(SAMPLE_DETAIL)
    assert result["tmdb_id"] == 550
    assert result["title"] == "Fight Club"
    assert result["runtime"] == 139
    assert result["language"] == "en"
    assert result["imdb_id"] == "tt0137523"
    # tmdb_data_json should be valid JSON
    parsed = json.loads(result["tmdb_data_json"])
    assert parsed["id"] == 550


def test_cache_miss_returns_none():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    result = _get_cache(db, "nonexistent_key")
    assert result is None


def test_cache_hit_returns_data():
    from datetime import datetime, timedelta
    from unittest.mock import MagicMock

    db = MagicMock()
    mock_row = MagicMock()
    mock_row.data_json = json.dumps({"result": "cached"})
    mock_row.expires_at = datetime.utcnow() + timedelta(hours=1)
    db.query.return_value.filter.return_value.first.return_value = mock_row

    result = _get_cache(db, "some_key")
    assert result == {"result": "cached"}
