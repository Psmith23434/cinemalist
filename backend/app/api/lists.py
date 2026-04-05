from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.list import MovieList
from app.models.list_item import ListItem
from app.schemas.list import ListCreate, ListUpdate, ListOut

router = APIRouter()


@router.get("/", response_model=list[ListOut])
async def list_lists(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieList).where(MovieList.deleted_at.is_(None)).order_by(MovieList.name)
    )
    lists = result.scalars().all()
    # Attach item counts
    out = []
    for lst in lists:
        count_result = await db.execute(
            select(func.count()).select_from(ListItem).where(ListItem.list_id == lst.id)
        )
        count = count_result.scalar() or 0
        lst_dict = {c.key: getattr(lst, c.key) for c in lst.__table__.columns}
        lst_dict["item_count"] = count
        out.append(ListOut(**lst_dict))
    return out


@router.post("/", response_model=ListOut, status_code=201)
async def create_list(data: ListCreate, db: AsyncSession = Depends(get_db)):
    lst = MovieList(**data.model_dump())
    db.add(lst)
    await db.flush()
    return ListOut(**{c.key: getattr(lst, c.key) for c in lst.__table__.columns}, item_count=0)


@router.patch("/{list_id}", response_model=ListOut)
async def update_list(list_id: int, data: ListUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieList).where(MovieList.id == list_id))
    lst = result.scalar_one_or_none()
    if not lst:
        raise HTTPException(status_code=404, detail="List not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(lst, field, value)
    await db.flush()
    return lst


@router.delete("/{list_id}", status_code=204)
async def delete_list(list_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieList).where(MovieList.id == list_id))
    lst = result.scalar_one_or_none()
    if not lst or lst.is_system:
        raise HTTPException(status_code=404, detail="List not found or cannot delete system list")
    await db.delete(lst)


@router.post("/{list_id}/items/{entry_id}", status_code=201)
async def add_to_list(list_id: int, entry_id: int, db: AsyncSession = Depends(get_db)):
    item = ListItem(list_id=list_id, entry_id=entry_id)
    db.add(item)
    await db.flush()
    return {"status": "added"}


@router.delete("/{list_id}/items/{entry_id}", status_code=204)
async def remove_from_list(list_id: int, entry_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ListItem).where(ListItem.list_id == list_id, ListItem.entry_id == entry_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not in list")
    await db.delete(item)
