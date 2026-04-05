from pydantic import BaseModel


class GenreRead(BaseModel):
    id: int
    tmdb_id: int | None = None
    name: str

    model_config = {"from_attributes": True}
