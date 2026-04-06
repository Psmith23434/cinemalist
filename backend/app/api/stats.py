from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from app.core.database import get_db
from app.models.entry import Entry
from app.models.movie import Movie
from app.models.movie_genre import MovieGenre
from app.models.genre import Genre
from app.schemas.stats import StatsOverview, GenreStat, YearStat, RatingDistribution

router = APIRouter()


@router.get("/overview", response_model=StatsOverview)
async def stats_overview(db: AsyncSession = Depends(get_db)):
    """Aggregate statistics for the user's library."""

    # Totals
    watched_count = await db.scalar(
        select(func.count(Entry.id)).where(Entry.watched == True, Entry.deleted_at.is_(None))
    )
    watchlisted_count = await db.scalar(
        select(func.count(Entry.id)).where(Entry.is_watchlisted == True, Entry.deleted_at.is_(None))
    )
    favorites_count = await db.scalar(
        select(func.count(Entry.id)).where(Entry.is_favorite == True, Entry.deleted_at.is_(None))
    )
    avg_rating = await db.scalar(
        select(func.avg(Entry.rating)).where(
            Entry.rating.isnot(None), Entry.deleted_at.is_(None)
        )
    )
    total_runtime = await db.scalar(
        select(func.sum(Movie.runtime))
        .join(Entry, Entry.movie_id == Movie.id)
        .where(Entry.watched == True, Entry.deleted_at.is_(None), Movie.runtime.isnot(None))
    )

    # Top genres
    genre_rows = await db.execute(
        select(Genre.name, func.count(MovieGenre.movie_id).label("cnt"))
        .join(MovieGenre, MovieGenre.genre_id == Genre.id)
        .join(Movie, Movie.id == MovieGenre.movie_id)
        .join(Entry, Entry.movie_id == Movie.id)
        .where(Entry.watched == True, Entry.deleted_at.is_(None))
        .group_by(Genre.name)
        .order_by(func.count(MovieGenre.movie_id).desc())
        .limit(10)
    )
    top_genres = [GenreStat(genre=row.name, count=row.cnt) for row in genre_rows]

    # By year watched — Bug 8 fix: func.extract works on both SQLite and PostgreSQL.
    # func.strftime("%Y", ...) was SQLite-only and would break on Phase 7 PostgreSQL migration.
    # func.extract returns a float on SQLite (e.g. 2026.0), cast to int before use.
    year_expr = func.extract("year", Entry.first_watched_at)
    year_rows = await db.execute(
        select(
            year_expr.label("yr"),
            func.count(Entry.id).label("cnt"),
            func.avg(Entry.rating).label("avg"),
        )
        .where(Entry.watched == True, Entry.deleted_at.is_(None), Entry.first_watched_at.isnot(None))
        .group_by(year_expr)
        .order_by(year_expr)
    )
    by_year = [
        YearStat(year=int(row.yr), count=row.cnt, avg_rating=round(row.avg, 2) if row.avg else None)
        for row in year_rows
    ]

    # Rating distribution (buckets: 1-2, 3-4, 5-6, 7-8, 9-10)
    buckets = [(1, 2), (3, 4), (5, 6), (7, 8), (9, 10)]
    rating_dist = []
    for low, high in buckets:
        cnt = await db.scalar(
            select(func.count(Entry.id)).where(
                Entry.rating >= low, Entry.rating <= high, Entry.deleted_at.is_(None)
            )
        )
        rating_dist.append(RatingDistribution(bucket=f"{low}-{high}", count=cnt or 0))

    return StatsOverview(
        total_watched=watched_count or 0,
        total_watchlisted=watchlisted_count or 0,
        total_favorites=favorites_count or 0,
        average_rating=round(avg_rating, 2) if avg_rating else None,
        top_genres=top_genres,
        by_year=by_year,
        rating_distribution=rating_dist,
        total_runtime_minutes=total_runtime,
    )
