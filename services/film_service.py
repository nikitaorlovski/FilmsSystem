from fastapi import Depends, UploadFile
from domain.exceptions import FilmNotFound
from domain.interfaces.film_repository import IFilmRepository
from repositories.film_repository import get_film_repo, FilmRepository
from schemas.films import Film, NewFilm
from services.image_service import ImageService, get_image_service


class FilmService:
    def __init__(
        self,
        repository: IFilmRepository,
        image_service: ImageService,
    ):
        self.repository = repository
        self.image_service = image_service

    async def get_all(self) -> list[Film]:
        return await self.repository.get_all_films()

    async def get_by_id(self, id: int) -> Film:
        return await self.repository.get_by_id(id)

    async def add_film(self, film: NewFilm, image: UploadFile | None = None):
        image_url = None
        if image:
            image_url = await self.image_service.upload(image)
        return await self.repository.add_film(film, image_url)

    async def delete_film(self, id: int):
        film = await self.repository.get_by_id(id)

        if film is None:
            raise FilmNotFound()

        if film.image_url:
            await self.image_service.delete(image_url=film.image_url)

        await self.repository.delete(id)
        return "Film deleted"

    async def get_sessions(self, film_id: int):
        film = await self.repository.get_by_id(film_id)
        if film is None:
            raise FilmNotFound()

        return await self.repository.get_sessions_by_film_id(film_id)

    async def update_film(
            self,
            film_id: int,
            film_data: NewFilm,
            image: UploadFile | None = None,
            is_active: bool = True
    ) -> Film:
        # Проверяем существование фильма
        existing_film = await self.repository.get_by_id(film_id)
        if existing_film is None:
            raise FilmNotFound()

        image_url = existing_film.image_url

        # Если загружено новое изображение
        if image:
            # Удаляем старое изображение если оно есть
            if existing_film.image_url:
                await self.image_service.delete(image_url=existing_film.image_url)
            # Загружаем новое изображение
            image_url = await self.image_service.upload(image)

        return await self.repository.update_film(
            film_id=film_id,
            film_data=film_data,
            image_url=image_url,
            is_active=is_active
        )



async def get_film_service(
    repo: FilmRepository = Depends(get_film_repo),
    image_service: ImageService = Depends(get_image_service),
):
    return FilmService(repo, image_service)
