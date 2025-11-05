from pydantic import BaseModel, Field


class NewFilm(BaseModel):
    title: str
    genre: str
    duration: int = Field(..., ge=0)
    rating: float = Field(..., ge=0, le=10)
    description: str | None = None


class Film(BaseModel):
    id: int
    title: str
    genre: str
    duration: int
    rating: float
    description: str | None = None
    is_active: bool
    image_url: str | None = None