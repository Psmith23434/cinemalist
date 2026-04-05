from pydantic import BaseModel
from typing import Optional


class GenreStat(BaseModel):
    genre: str
    count: int
    avg_rating: Optional[float] = None


class YearStat(BaseModel):
    year: int
    count: int
    avg_rating: Optional[float] = None


class StatsOut(BaseModel):
    total_watched: int
    total_watchlisted: int
    total_favorites: int
    average_rating: Optional[float] = None
    total_runtime_minutes: Optional[int] = None
    total_runtime_hours: Optional[float] = None
    genres: list[GenreStat] = []
    by_year: list[YearStat] = []
    most_watched_genre: Optional[str] = None
    highest_rated_genre: Optional[str] = None
