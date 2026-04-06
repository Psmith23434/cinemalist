"""
AI router — Phase 5.

Endpoints
---------
  GET  /api/ai/recommend          — personalised recommendations based on watch history
  GET  /api/ai/stats-report       — narrative summary of user stats (German prose)
  POST /api/ai/suggest-tags       — auto-suggest tags for a movie by tmdb_id or entry_id
  GET  /api/ai/search?q=          — natural language search over the user's library

All endpoints return a 503 with a clear message when LLM_API_KEY is not set,
so the app is fully usable without AI configured.
"""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.entry import Entry
from app.models.movie import Movie
from app.models.movie_genre import MovieGenre
from app.models.genre import Genre
from app.services import llm as llm_service
from app.api.stats import get_stats  # reuse existing stats endpoint logic

router = APIRouter()


# ── Helper: build entry dicts for LLM prompts ───────────────────────────────

async def _load_entry_dicts(db: AsyncSession) -> list[dict[str, Any]]:
    """Load all non-deleted entries with their movie + genres into plain dicts."""
    result = await db.execute(
        select(Entry)
        .where(Entry.deleted_at.is_(None))
        .options(
            selectinload(Entry.movie).selectinload(Movie.genres).selectinload(MovieGenre.genre)
        )
        .order_by(Entry.first_watched_at.desc().nullslast())
    )
    entries = result.scalars().all()

    dicts = []
    for e in entries:
        movie = e.movie
        if not movie:
            continue
        cast = []
        if movie.cast_top5:
            try:
                cast = json.loads(movie.cast_top5)
            except (json.JSONDecodeError, TypeError):
                cast = []
        genres = [mg.genre.name for mg in movie.genres if mg.genre]
        dicts.append({
            "entry_id": e.id,
            "tmdb_id": movie.tmdb_id,
            "title": movie.title,
            "year": movie.year,
            "overview": movie.overview,
            "rating": e.rating,
            "genres": genres,
            "director": movie.director,
            "cast_top5": cast,
            "notes": e.notes,
            "is_favorite": e.is_favorite,
        })
    return dicts


# ── GET /api/ai/recommend ───────────────────────────────────────────────────

@router.get("/recommend")
async def get_recommendations(
    db: AsyncSession = Depends(get_db),
):
    """
    Return 8 personalised movie recommendations based on the user's watch history.

    Reads all watched entries, builds a compact prompt, and asks the LLM to
    recommend films the user hasn't seen yet. Responses are in German.

    Returns:
        {"recommendations": [{"title": str, "year": int|None, "reason": str}]}
    """
    entries = await _load_entry_dicts(db)
    recommendations = await llm_service.recommend(entries)
    return {"recommendations": recommendations, "based_on": len(entries)}


# ── GET /api/ai/stats-report ───────────────────────────────────────────────

@router.get("/stats-report")
async def get_stats_report(
    db: AsyncSession = Depends(get_db),
):
    """
    Return a short German narrative paragraph summarising the user's movie stats.

    Fetches live stats from the stats endpoint and asks the LLM to write
    a 2-4 sentence personal summary.

    Returns:
        {"report": str}
    """
    stats = await get_stats(db=db)
    report = await llm_service.stats_report(stats)
    return {"report": report}


# ── POST /api/ai/suggest-tags ──────────────────────────────────────────────

@router.post("/suggest-tags")
async def suggest_tags_for_movie(
    movie_id: int = Query(..., description="Local movie ID (from movies table)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Suggest 5-8 German tags for a movie based on its metadata.

    Looks up the movie by its local DB id, builds a metadata dict,
    and asks the LLM to suggest relevant tags.

    Returns:
        {"movie_id": int, "title": str, "suggested_tags": [str, ...]}
    """
    movie: Movie | None = (
        await db.execute(
            select(Movie)
            .where(Movie.id == movie_id)
            .options(selectinload(Movie.genres).selectinload(MovieGenre.genre))
        )
    ).scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    cast = []
    if movie.cast_top5:
        try:
            cast = json.loads(movie.cast_top5)
        except (json.JSONDecodeError, TypeError):
            cast = []

    movie_dict = {
        "title": movie.title,
        "year": movie.year,
        "overview": movie.overview,
        "genres": [mg.genre.name for mg in movie.genres if mg.genre],
        "director": movie.director,
        "cast_top5": cast,
    }

    tags = await llm_service.suggest_tags(movie_dict)
    return {"movie_id": movie_id, "title": movie.title, "suggested_tags": tags}


# ── GET /api/ai/search ───────────────────────────────────────────────────────

@router.get("/search")
async def natural_language_search(
    q: str = Query(..., min_length=2, description="Natural language search query in German or English"),
    db: AsyncSession = Depends(get_db),
):
    """
    Search the user's library using natural language.

    Examples (German or English):
        "Actionfilme aus den 90ern die ich mit 8+ bewertet habe"
        "Etwas mit Brad Pitt"
        "Mind-bending sci-fi movies"

    Loads all entries, sends them + the query to the LLM, returns matching entries.

    Returns:
        {"query": str, "results": [{entry dict}, ...], "count": int}
    """
    entries = await _load_entry_dicts(db)
    results = await llm_service.nl_search(query=q, entries=entries)
    return {"query": q, "results": results, "count": len(results)}
