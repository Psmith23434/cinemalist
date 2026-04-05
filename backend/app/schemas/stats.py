from pydantic import BaseModel
from typing import Dict, List, Optional


class GenreStat(BaseModel):
    genre: str
    count: int


class YearStat(BaseModel):
    year: int
    count: int
    avg_rating: Optional[float] = None


class RatingDistribution(BaseModel):
    bucket: str   # e.g. "9-10"
    count: int


class StatsOverview(BaseModel):
    total_watched: int
    total_watchlisted: int
    total_favorites: int
    average_rating: Optional[float] = None
    top_genres: List[GenreStat] = []
    by_year: List[YearStat] = []
    rating_distribution: List[RatingDistribution] = []
    total_runtime_minutes: Optional[int] = None
