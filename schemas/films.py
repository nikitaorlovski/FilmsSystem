from pydantic import BaseModel, Field
from enum import Enum

class FilmGenre(str, Enum):
    ACTION = "Боевик"
    COMEDY = "Комедия"
    DRAMA = "Драма"
    THRILLER = "Триллер"
    FANTASY = "Фэнтези"
    SCI_FI = "Фантастика"
    HORROR = "Ужасы"
    ROMANCE = "Романтика"
    ADVENTURE = "Приключения"
    DETECTIVE = "Детектив"
    ANIMATION = "Мультфильм"
    DOCUMENTARY = "Документальный"
    HISTORICAL = "Исторический"
    BIOGRAPHY = "Биография"
    FAMILY = "Семейный"

class NewFilm(BaseModel):
    title: str
    genre: FilmGenre
    duration: int = Field(..., ge=0)
    rating: float = Field(..., ge=0, le=10)
    description: str | None = None

class Film(BaseModel):
    id: int
    title: str
    genre: FilmGenre
    duration: int
    rating: float
    description: str | None = None
    is_active: bool
    image_url: str | None = None