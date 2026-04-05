from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.tmdb_cache import TmdbCache
from app.core.config import settings
from datetime import datetime, timezone, timedelta
import httpx
import json

router = APIRouter()

TMDB_CACHE_TTL_DAYS = 7


async def _tmdb_get(path: str, params: dict, db: AsyncSession) -> dict:
    """Fetch from TMDb with local DB caching."""
    cache_key = path + "::" + json.dumps(params, sort_keys=True)

    # Check cache
    cached = (await db.execute(select(TmdbCache).where(TmdbCache.cache_key == cache_key))).scalar_one_or_none()
    if cached and cached.expires_at and cached.expires_at > datetime.now(timezone.utc):
        return json.loads(cached.data_json)

    # Fetch from TMDb
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.TMDB_BASE_URL}{path}",
            params={"api_key": settings.TMDB_API_KEY, **params},
            timeout=10.0,
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"TMDb error: {resp.status_code}")

    data = resp.json()
    expires_at = datetime.now(timezone.utc) + timedelta(days=TMDB_CACHE_TTL_DAYS)

    # Upsert cache
    if cached:
        cached.data_json = json.dumps(data)
        cached.expires_at = expires_at
        cached.fetched_at = datetime.now(timezone.utc)
    else:
        db.add(TmdbCache(cache_key=cache_key, data_json=json.dumps(data), expires_at=expires_at))
    await db.flush()

    return data


@router.get("/tmdb")
async def search_tmdb(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
):
    """Search TMDb for movies by title. Results cached for 7 days."""
    data = await _tmdb_get("/search/movie", {"query": q, "page": page, "include_adult": "false"}, db)
    return data


@router.get("/tmdb/{tmdb_id}")
async def get_tmdb_movie(
    tmdb_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get full movie details from TMDb (cast, crew, genres, etc.)."""
    data = await _tmdb_get(f"/movie/{tmdb_id}", {"append_to_response": "credits"}, db)
    return data
