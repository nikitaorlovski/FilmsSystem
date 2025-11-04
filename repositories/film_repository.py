from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from database.db import get_session
from schemas.films import Film, NewFilm
from domain.interfaces.film_repository import IFilmRepository


class FilmRepository(IFilmRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_films(self) -> list[Film]:
        query = text(
            """
            SELECT id, title, genre, duration, rating, description, image_url
            FROM films
            ORDER BY rating DESC
        """
        )

        result = await self.session.execute(query)
        rows = result.fetchall()

        return [Film(**row._mapping) for row in rows]

    async def add_film(self, film: NewFilm, image_url: str | None = None) -> Film:
        query = text(
            """
            INSERT INTO films (title, genre, duration, rating, description, image_url)
            VALUES (:title, :genre, :duration, :rating, :description, :image_url)
            RETURNING id, title, genre, duration, rating, description, image_url
        """
        )

        values = film.model_dump()
        values["image_url"] = image_url

        result = await self.session.execute(query, values)
        row = result.fetchone()
        await self.session.commit()

        return Film(**dict(row._mapping))

    async def get_by_id(self, id: int) -> Film | None:
        result = await self.session.execute(
            text(
                """
                SELECT id, title, genre, duration, rating, description, image_url
                FROM films
                WHERE id = :id
            """
            ),
            {"id": id},
        )
        row = result.fetchone()

        if row is None:
            return None

        return Film(**row._mapping)

    async def delete(self, id: int) -> None:
        await self.session.execute(
            text("DELETE FROM films WHERE id = :id"),
            {"id": id},
        )
        await self.session.commit()


async def get_film_repo(session: AsyncSession = Depends(get_session)):
    return FilmRepository(session)
