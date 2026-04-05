"""
Search router — /api/search

Endpoints
---------
GET  /api/search/tmdb              Search TMDb by title (cached 7 days)
GET  /api/search/tmdb/{tmdb_id}    Full TMDb movie details (cached 7 days)
POST /api/search/tmdb/import       Import a TMDb movie into the local DB
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.models.movie import Movie
from app.schemas.movie import MovieOut
from app.services import tmdb as tmdb_service
from pydantic import BaseModel

router = APIRouter()


# ── Pydantic schemas local to this router ─────────────────────────────────────

class TmdbImportRequest(BaseModel):
    tmdb_id: int


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/tmdb", summary="Search TMDb by title")
async def search_tmdb(
    q: str = Query(..., min_length=1, description="Movie title to search"),
    page: int = Query(1, ge=1, description="TMDb results page"),
    db: AsyncSession = Depends(get_db),
):
    """
    Proxy to TMDb /search/movie.  Results are cached locally for 7 days.
    Returns the raw TMDb response so the UI can display poster thumbnails
    and select which film to import.
    """
    return await tmdb_service.search_movies(q, page, db)


@router.get("/tmdb/{tmdb_id}", summary="Get full TMDb movie details")
async def get_tmdb_details(
    tmdb_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the full TMDb detail payload including credits.
    Cached locally for 7 days.
    """
    return await tmdb_service.get_movie_details(tmdb_id, db)


@router.post("/tmdb/import", response_model=MovieOut, status_code=201,
             summary="Import a TMDb movie into your library")
async def import_from_tmdb(
    body: TmdbImportRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Fetches full details from TMDb and upserts the movie into the local
    `movies` table, including all genres via the `movie_genres` join table.

    - If the movie already exists (same `tmdb_id`) it is **updated** in-place.
    - Returns the full `MovieOut` schema so the UI can immediately display
      the imported movie.

    After calling this endpoint you can create a personal `entry` via
    `POST /api/entries/` referencing the returned `movie_id`.
    """
    movie: Movie = await tmdb_service.import_movie(body.tmdb_id, db)
    # Eagerly reload genres relationship so response_model can serialise it
    await db.refresh(movie, attribute_names=["genres"])
    return movie
