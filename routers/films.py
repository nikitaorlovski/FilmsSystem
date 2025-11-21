from fastapi import APIRouter, Depends, Form, File, UploadFile, status, HTTPException

from core.auth import admin_required
from domain.exceptions import FilmNotFound
from services.film_service import FilmService, get_film_service
from schemas.films import Film, NewFilm

router = APIRouter(prefix="/films", tags=["Films"])


@router.get("/", response_model=list[Film])
async def get_films(service: FilmService = Depends(get_film_service)) -> list[Film]:
    return await service.get_all()

@router.get("/{id}", response_model=Film)
async def get_film(id: int, service: FilmService = Depends(get_film_service)) -> Film:
    film = await service.get_by_id(id)
    if not film:
        raise HTTPException(status_code=404, detail="Film not found")
    return film

@router.put("/{id}", dependencies=[Depends(admin_required)])
async def update_film(
        id: int,
        title: str = Form(...),
        genre: str = Form(...),
        duration: int = Form(...),
        rating: float = Form(...),
        description: str = Form(...),
        is_active: bool = Form(True),
        image: UploadFile | None = File(None),
        service: FilmService = Depends(get_film_service),
):
    try:
        print(f"Обновление фильма {id} с данными:")
        print(f"Title: {title}, Genre: {genre}, Duration: {duration}")
        print(f"Rating: {rating}, Active: {is_active}")

        updated_film = NewFilm(
            title=title,
            genre=genre,
            duration=duration,
            rating=rating,
            description=description,
        )
        result = await service.update_film(id, updated_film, image, is_active)
        print(f"Фильм успешно обновлен: {result}")
        return result
    except FilmNotFound:
        raise HTTPException(status_code=404, detail="Film not found")
    except Exception as e:
        print(f"Ошибка при обновлении фильма: {str(e)}")
        print(f"Тип ошибки: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


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
