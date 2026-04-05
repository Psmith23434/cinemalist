"""TMDb API service — all external TMDb calls go through here.

Every result is cached in the local `tmdb_cache` table for CACHE_TTL_DAYS days
so repeated lookups are instant and offline-resilient.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.tmdb_cache import TmdbCache

CACHE_TTL_DAYS = 7
POSTER_SIZES = {
    "thumb": "w185",
    "small": "w342",
    "medium": "w500",
    "large": "w780",
    "original": "original",
}


class TMDbService:
    """Async wrapper around the TMDb v3 REST API."""

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def poster_url(self, path: str | None, size: str = "medium") -> str | None:
        """Build a full poster/backdrop URL from a TMDb path.

        Args:
            path:  TMDb image path, e.g. ``/abc123.jpg``
            size:  One of thumb / small / medium / large / original
        """
        if not path:
            return None
        size_slug = POSTER_SIZES.get(size, "w500")
        return f"{settings.TMDB_IMAGE_BASE}/{size_slug}{path}"

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    async def search_movies(
        self,
        query: str,
        page: int = 1,
        db: AsyncSession = None,
    ) -> dict[str, Any]:
        """Search TMDb for movies by title.

        Returns the raw TMDb paginated response with poster URLs injected
        into each result under the key ``poster_url``.
        """
        data = await self._get(
            "/search/movie",
            {"query": query, "page": page, "include_adult": "false"},
            db,
        )
        # Inject resolved poster URLs so callers don't need to do it
        for movie in data.get("results", []):
            movie["poster_url"] = self.poster_url(movie.get("poster_path"))
            movie["backdrop_url"] = self.poster_url(movie.get("backdrop_path"), "large")
        return data

    # ------------------------------------------------------------------
    # Movie detail
    # ------------------------------------------------------------------

    async def get_movie_detail(
        self,
        tmdb_id: int,
        db: AsyncSession = None,
    ) -> dict[str, Any]:
        """Fetch full movie detail including credits from TMDb.

        Injects ``poster_url``, ``backdrop_url``, ``director``, and
        ``cast_top5`` (list of up to 5 cast member names) into the result.
        """
        data = await self._get(
            f"/movie/{tmdb_id}",
            {"append_to_response": "credits"},
            db,
        )
        data["poster_url"] = self.poster_url(data.get("poster_path"))
        data["backdrop_url"] = self.poster_url(data.get("backdrop_path"), "large")

        # Extract director
        crew = data.get("credits", {}).get("crew", [])
        directors = [p["name"] for p in crew if p.get("job") == "Director"]
        data["director"] = ", ".join(directors) if directors else None

        # Extract top-5 cast
        cast = data.get("credits", {}).get("cast", [])
        data["cast_top5"] = [m["name"] for m in cast[:5]]

        return data

    # ------------------------------------------------------------------
    # Genres
    # ------------------------------------------------------------------

    async def get_genres(self, db: AsyncSession = None) -> list[dict]:
        """Fetch the TMDb movie genre list."""
        data = await self._get("/genre/movie/list", {"language": "en"}, db)
        return data.get("genres", [])

    # ------------------------------------------------------------------
    # Internal cache-aware HTTP layer
    # ------------------------------------------------------------------

    async def _get(
        self,
        path: str,
        params: dict,
        db: AsyncSession | None,
    ) -> dict[str, Any]:
        """Fetch ``path`` from TMDb, serving from DB cache when fresh."""
        cache_key = path + "::" + json.dumps(params, sort_keys=True)

        if db is not None:
            cached = (
                await db.execute(
                    select(TmdbCache).where(TmdbCache.cache_key == cache_key)
                )
            ).scalar_one_or_none()

            if (
                cached
                and cached.expires_at
                and cached.expires_at > datetime.now(timezone.utc)
            ):
                return json.loads(cached.data)

        # --- Live fetch ---
        if not settings.TMDB_API_KEY:
            raise HTTPException(
                status_code=503,
                detail="TMDB_API_KEY is not configured. Add it to backend/.env",
            )

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{settings.TMDB_BASE_URL}{path}",
                params={"api_key": settings.TMDB_API_KEY, **params},
            )

        if resp.status_code == 401:
            raise HTTPException(status_code=401, detail="Invalid TMDb API key")
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail=f"TMDb resource not found: {path}")
        if resp.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"TMDb returned HTTP {resp.status_code}",
            )

        data = resp.json()
        expires_at = datetime.now(timezone.utc) + timedelta(days=CACHE_TTL_DAYS)

        if db is not None:
            if cached:
                cached.data = json.dumps(data)
                cached.expires_at = expires_at
                cached.fetched_at = datetime.now(timezone.utc)
            else:
                db.add(
                    TmdbCache(
                        cache_key=cache_key,
                        data=json.dumps(data),
                        expires_at=expires_at,
                    )
                )
            await db.flush()

        return data


# Module-level singleton — import and use directly
tmdb = TMDbService()
