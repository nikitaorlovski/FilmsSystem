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


async def get_film_service(
    repo: FilmRepository = Depends(get_film_repo),
    image_service: ImageService = Depends(get_image_service),
):
    return FilmService(repo, image_service)
