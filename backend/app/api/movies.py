"""
POST /api/v1/movies/import/{tmdb_id}  — import a movie from TMDb into the local DB
GET  /api/v1/movies                   — list all locally-stored movies
GET  /api/v1/movies/{id}              — get one locally-stored movie
DELETE /api/v1/movies/{id}            — remove a movie from the local cache
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import tmdb as tmdb_service

router = APIRouter(prefix="/api/v1/movies", tags=["movies"])


# ---------------------------------------------------------------------------
# Helper: get-or-create a Movie row from TMDb data
# ---------------------------------------------------------------------------
def _upsert_movie(db: Session, tmdb_id: int) -> Any:
    """Fetch TMDb detail and upsert into the local `movies` table."""
    # Lazy import to avoid circular deps at module load time
    from app.models.movie import Movie  # type: ignore

    detail = tmdb_service.get_movie_detail(db, tmdb_id)
    movie_dict = tmdb_service.tmdb_detail_to_movie_dict(detail)

    movie = db.query(Movie).filter(Movie.tmdb_id == tmdb_id).first()
    if movie:
        # Refresh cached data
        for key, value in movie_dict.items():
            setattr(movie, key, value)
    else:
        movie = Movie(**movie_dict)
        db.add(movie)

    db.commit()
    db.refresh(movie)
    return movie, detail


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@router.post("/import/{tmdb_id}", status_code=201)
def import_movie(
    tmdb_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Any:
    """
    Import (or refresh) a movie from TMDb into the local database.
    The poster image is downloaded in the background so the response is immediate.
    """
    try:
        movie, detail = _upsert_movie(db, tmdb_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"TMDb import failed: {exc}") from exc

    # Download poster in the background — don't block the response
    poster_path = detail.get("poster_path")
    if poster_path:
        background_tasks.add_task(tmdb_service.download_poster, tmdb_id, poster_path)

    return {
        "id": movie.id,
        "tmdb_id": movie.tmdb_id,
        "title": movie.title,
        "release_date": str(movie.release_date) if movie.release_date else None,
        "poster_local": f"posters/{tmdb_id}.jpg" if poster_path else None,
        "message": "Movie imported successfully. Poster downloading in background.",
    }


@router.get("/")
def list_movies(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List all movies currently stored in the local database."""
    from app.models.movie import Movie  # type: ignore

    movies = db.query(Movie).offset(skip).limit(limit).all()
    return [
        {
            "id": m.id,
            "tmdb_id": m.tmdb_id,
            "title": m.title,
            "release_date": str(m.release_date) if m.release_date else None,
            "runtime": m.runtime,
            "vote_average": m.vote_average,
            "poster_path": m.poster_path,
            "overview": m.overview,
            "tagline": m.tagline,
            "language": m.language,
        }
        for m in movies
    ]


@router.get("/{movie_id}")
def get_movie(
    movie_id: int,
    db: Session = Depends(get_db),
) -> Any:
    """Get a single locally-stored movie by its local DB id."""
    from app.models.movie import Movie  # type: ignore

    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@router.delete("/{movie_id}", status_code=204)
def delete_movie(
    movie_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Remove a movie from the local cache (does not affect entries/ratings)."""
    from app.models.movie import Movie  # type: ignore

    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    db.delete(movie)
    db.commit()
