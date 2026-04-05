"""Search endpoints — TMDb movie search with local caching."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.tmdb import tmdb
from app.schemas.tmdb import TMDbSearchResponse, TMDbMovieDetail, TMDbMovieResult

router = APIRouter()


@router.get("/tmdb", response_model=TMDbSearchResponse, summary="Search TMDb for movies")
async def search_tmdb(
    q: str = Query(..., min_length=1, description="Movie title to search for"),
    page: int = Query(1, ge=1, description="Result page (TMDb paginates at 20/page)"),
    db: AsyncSession = Depends(get_db),
):
    """Search TMDb by title. Results are cached locally for 7 days.

    Each result includes a ready-to-use ``poster_url`` (w500) so the UI
    can render posters without any additional URL construction.
    """
    data = await tmdb.search_movies(query=q, page=page, db=db)

    results = [
        TMDbMovieResult.from_tmdb(item)
        for item in data.get("results", [])
    ]

    return TMDbSearchResponse(
        page=data.get("page", 1),
        total_results=data.get("total_results", 0),
        total_pages=data.get("total_pages", 1),
        results=results,
    )


@router.get(
    "/tmdb/{tmdb_id}",
    response_model=TMDbMovieDetail,
    summary="Get full TMDb movie detail",
)
async def get_tmdb_movie(
    tmdb_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Fetch full movie metadata from TMDb including cast, crew and genres.

    Also cached locally. Call this before importing a movie to preview
    what will be stored.
    """
    data = await tmdb.get_movie_detail(tmdb_id=tmdb_id, db=db)
    return TMDbMovieDetail.from_tmdb(data)
