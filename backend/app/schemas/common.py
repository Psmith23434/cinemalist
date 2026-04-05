"""Shared response helpers."""
from pydantic import BaseModel
from typing import Generic, TypeVar, List

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    total: int
    page: int
    per_page: int
    items: List[T]


class MessageResponse(BaseModel):
    message: str
    ok: bool = True
