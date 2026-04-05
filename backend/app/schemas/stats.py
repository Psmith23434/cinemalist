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


class RatingBucketStat(BaseModel):
    """Count of watched entries whose rating falls within [low, high)."""
    label: str          # e.g. "0–2", "2–4", ..., "8–10"
    low: float
    high: float
    count: int


class StatsOut(BaseModel):
    total_watched: int
    total_watchlisted: int
    total_favorites: int
    average_rating: Optional[float] = None
    total_runtime_minutes: Optional[int] = None
    total_runtime_hours: Optional[float] = None
    genres: list[GenreStat] = []
    by_year: list[YearStat] = []
    rating_breakdown: list[RatingBucketStat] = []
    most_watched_genre: Optional[str] = None
    highest_rated_genre: Optional[str] = None
