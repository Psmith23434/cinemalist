from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class WatchEventCreate(BaseModel):
    entry_id: int
    watched_at: Optional[datetime] = None
    platform: Optional[str] = None
    note: Optional[str] = None


class WatchEventRead(BaseModel):
    id: int
    uuid: str
    entry_id: int
    watched_at: Optional[datetime] = None
    platform: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
