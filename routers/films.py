from fastapi import APIRouter, Depends, Form, File, UploadFile, status, HTTPException

from core.auth import admin_required
from domain.exceptions import FilmNotFound
from services.film_service import FilmService, get_film_service
from schemas.films import Film, NewFilm

router = APIRouter(prefix="/films", tags=["Films"])


@router.get("/", response_model=list[Film])
async def get_films(service: FilmService = Depends(get_film_service)) -> list[Film]:
    return await service.get_all()


@router.post("/", dependencies=[Depends(admin_required)])
async def add_film(
    title: str = Form(...),
    genre: str = Form(...),
    duration: int = Form(...),
    rating: float = Form(...),
    description: str = Form(...),
    image: UploadFile | None = File(None),
    service: FilmService = Depends(get_film_service),
):
    new_film = NewFilm(
        title=title,
        genre=genre,
        duration=duration,
        rating=rating,
        description=description,
    )

    return await service.add_film(new_film, image)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(admin_required)],
)
async def delete_film(id: int, service: FilmService = Depends(get_film_service)):
    try:
        return await service.delete_film(id)
    except FilmNotFound:
        raise HTTPException(status_code=404, detail="Film not found")


@router.get("/{id}/sessions")
async def get_sessions(
    id: int,
    service: FilmService = Depends(get_film_service),
):
    try:
        return await service.get_sessions(id)
    except FilmNotFound:
        raise HTTPException(status_code=404, detail="Film not found")
