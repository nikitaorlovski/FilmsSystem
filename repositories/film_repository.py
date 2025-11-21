from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from database.db import get_session
from domain.exceptions import FilmNotFound
from schemas.films import Film, NewFilm
from domain.interfaces.film_repository import IFilmRepository
from schemas.sessions import Session


class FilmRepository(IFilmRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_films(self) -> list[Film]:
        query = text(
            """
            SELECT id, title, genre, duration, rating, description, image_url, is_active
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
            RETURNING id, title, genre, duration, rating, description, image_url, is_active
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
                SELECT id, title, genre, duration, rating, description, image_url, is_active
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

    async def update_film(
            self,
            film_id: int,
            film_data: NewFilm,
            image_url: str | None = None,
            is_active: bool = True
    ) -> Film:
        query = text(
            """
            UPDATE films 
            SET title = :title, genre = :genre, duration = :duration, rating = :rating, 
                description = :description, is_active = :is_active, image_url = :image_url
            WHERE id = :film_id
            RETURNING id, title, genre, duration, rating, description, image_url, is_active
            """
        )

        values = {
            "title": film_data.title,
            "genre": film_data.genre,
            "duration": film_data.duration,
            "rating": film_data.rating,
            "description": film_data.description,
            "is_active": is_active,
            "image_url": image_url,
            "film_id": film_id
        }

        try:
            result = await self.session.execute(query, values)
            row = result.fetchone()
            await self.session.commit()

            if not row:
                raise FilmNotFound()

            return Film(**dict(row._mapping))

        except Exception as e:
            await self.session.rollback()
            raise e

    async def delete(self, id: int) -> None:
        await self.session.execute(
            text("DELETE FROM films WHERE id = :id"),
            {"id": id},
        )
        await self.session.commit()

    async def get_sessions_by_film_id(self, film_id: int) -> list[Session]:
        query = text(
            """
            SELECT
                id,
                film_id,
                hall_id,
                start_time,
                price,
                total_seats,
                available_seats,
                created_at
            FROM sessions
            WHERE film_id = :film_id
            ORDER BY start_time;
            """
        )

        result = await self.session.execute(query, {"film_id": film_id})
        rows = result.fetchall()

        return [Session(**row._mapping) for row in rows]


async def get_film_repo(session: AsyncSession = Depends(get_session)):
    return FilmRepository(session)
