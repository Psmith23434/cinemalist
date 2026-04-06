"""
Search router.

Endpoints
---------
  GET  /api/search/tmdb?q=&page=&lang=    — search TMDb, return raw results
  POST /api/search/tmdb/import/{tmdb_id}?lang=  — import movie from TMDb into local DB

Language parameter
------------------
  Both endpoints accept an optional `lang` query param (BCP-47).
  Default is "de-DE" so the frontend can pass nothing and get German results.
  The frontend language toggle sends lang=de-DE or lang=en-US.
"""
from __future__ import annotations

import json
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.tmdb_cache import TmdbCache
from app.services import tmdb as tmdb_service

router = APIRouter()


@router.get("/tmdb")
async def search_tmdb(
    q: str = Query(..., min_length=1, description="Search query (German or English title)"),
    page: int = Query(1, ge=1),
    lang: str = Query("de-DE", description="BCP-47 language code, e.g. de-DE or en-US"),
    db: AsyncSession = Depends(get_db),
):
    """Search TMDb by movie title.

    Returns raw TMDb search results. The `lang` parameter controls the language
    of returned titles and overviews (default: de-DE).
    Searching by German title (e.g. 'Der Pate') works correctly with de-DE.
    """
    data = await tmdb_service.search_movies(q=q, page=page, db=db, lang=lang)
    return data


@router.post("/tmdb/import/{tmdb_id}")
async def import_from_tmdb(
    tmdb_id: int,
    lang: str = Query("de-DE", description="BCP-47 language code for stored overview/title"),
    db: AsyncSession = Depends(get_db),
):
    """Import a movie from TMDb into the local database.

    Uses the tmdb service layer (single implementation, no duplication).
    The `lang` parameter controls which language the overview/tagline are
    stored in (default: de-DE).
    """
    movie = await tmdb_service.import_movie(tmdb_id=tmdb_id, db=db, lang=lang)
    await db.commit()
    await db.refresh(movie)
    return {
        "id": movie.id,
        "tmdb_id": movie.tmdb_id,
        "title": movie.title,
        "year": movie.year,
        "overview": movie.overview,
        "poster_path": movie.poster_path,
        "backdrop_path": movie.backdrop_path,
        "language": movie.language,
    }
