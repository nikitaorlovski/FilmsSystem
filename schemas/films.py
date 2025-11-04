from pydantic import BaseModel

class NewFilm(BaseModel):
    title: str
    genre: str
    duration: int
    rating: float
    description: str


class Film(BaseModel):
    id: int
    title: str
    genre: str
    duration: int
    rating: float
    description: str
    image_url: str | None
