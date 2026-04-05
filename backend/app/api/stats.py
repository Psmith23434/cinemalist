from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models.entry import Entry
from app.models.movie import Movie
from app.models.movie_genre import MovieGenre
from app.models.genre import Genre
from app.schemas.stats import StatsOut, GenreStat, YearStat

router = APIRouter()


@router.get("/", response_model=StatsOut)
async def get_stats(db: AsyncSession = Depends(get_db)):
    # Total watched
    total_watched = (await db.execute(
        select(func.count()).select_from(Entry)
        .where(Entry.watched == True, Entry.deleted_at.is_(None))
    )).scalar() or 0

    total_watchlisted = (await db.execute(
        select(func.count()).select_from(Entry)
        .where(Entry.is_watchlisted == True, Entry.deleted_at.is_(None))
    )).scalar() or 0

    total_favorites = (await db.execute(
        select(func.count()).select_from(Entry)
        .where(Entry.is_favorite == True, Entry.deleted_at.is_(None))
    )).scalar() or 0

    avg_rating = (await db.execute(
        select(func.avg(Entry.rating)).where(Entry.rating.isnot(None), Entry.deleted_at.is_(None))
    )).scalar()

    # Total runtime
    total_runtime = (await db.execute(
        select(func.sum(Movie.runtime))
        .join(Entry, Entry.movie_id == Movie.id)
        .where(Entry.watched == True, Entry.deleted_at.is_(None))
    )).scalar() or 0

    # Genre breakdown
    genre_rows = (await db.execute(
        select(Genre.name, func.count(Entry.id).label("cnt"), func.avg(Entry.rating).label("avg_r"))
        .join(MovieGenre, MovieGenre.genre_id == Genre.id)
        .join(Movie, Movie.id == MovieGenre.movie_id)
        .join(Entry, Entry.movie_id == Movie.id)
        .where(Entry.watched == True, Entry.deleted_at.is_(None))
        .group_by(Genre.name)
        .order_by(func.count(Entry.id).desc())
    )).all()

    genre_stats = [GenreStat(genre=r.name, count=r.cnt, avg_rating=round(r.avg_r, 2) if r.avg_r else None) for r in genre_rows]

    # By watch year
    year_rows = (await db.execute(
        select(
            func.strftime("%Y", Entry.first_watched_at).label("yr"),
            func.count(Entry.id).label("cnt"),
            func.avg(Entry.rating).label("avg_r"),
        )
        .where(Entry.watched == True, Entry.first_watched_at.isnot(None), Entry.deleted_at.is_(None))
        .group_by(func.strftime("%Y", Entry.first_watched_at))
        .order_by(func.strftime("%Y", Entry.first_watched_at))
    )).all()

    year_stats = [YearStat(year=int(r.yr), count=r.cnt, avg_rating=round(r.avg_r, 2) if r.avg_r else None) for r in year_rows]

    return StatsOut(
        total_watched=total_watched,
        total_watchlisted=total_watchlisted,
        total_favorites=total_favorites,
        average_rating=round(avg_rating, 2) if avg_rating else None,
        total_runtime_minutes=total_runtime,
        total_runtime_hours=round(total_runtime / 60, 1) if total_runtime else None,
        genres=genre_stats,
        by_year=year_stats,
        most_watched_genre=genre_stats[0].genre if genre_stats else None,
        highest_rated_genre=max(genre_stats, key=lambda g: g.avg_rating or 0).genre if genre_stats else None,
    )
