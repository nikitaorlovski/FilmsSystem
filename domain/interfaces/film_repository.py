from typing import Protocol
from schemas.films import Film, NewFilm
from schemas.sessions import Session


class IFilmRepository(Protocol):

    async def get_all_films(self) -> list[Film]: ...

    async def add_film(self, film: NewFilm, image_url: str | None = None) -> Film: ...

    async def get_by_id(self, id: int) -> Film | None: ...

    async def delete(self, id: int) -> None: ...

    async def get_sessions_by_film_id(self, film_id: int) -> list[Session]: ...
    async def update_film(
            self,
            film_id: int,
            film_data: NewFilm,
            image_url: str | None = None,
            is_active: bool = True
    ) -> Film: ...
