from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class ListCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_public: bool = False


class ListUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None


class ListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    uuid: str
    name: str
    description: Optional[str] = None
    is_public: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime
    item_count: int = 0
