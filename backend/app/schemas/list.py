from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from .entry import EntryRead


class MovieListCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_public: bool = False


class MovieListUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None


class MovieListRead(BaseModel):
    id: int
    uuid: str
    name: str
    description: Optional[str] = None
    is_public: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MovieListDetail(MovieListRead):
    """Full list including its items."""
    items: List[EntryRead] = []
