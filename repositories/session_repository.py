from domain.exceptions import SessionConflictError
from fastapi import Depends, HTTPException
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import DBAPIError
import asyncpg
from domain.exceptions import FilmNotFound, HallNotFound
from database.db import get_session
from schemas.sessions import Session, NewSession


class SessionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_session(self, data: NewSession) -> Session:

        film_exists = await self.session.execute(
            text("SELECT 1 FROM films WHERE id = :id"), {"id": data.film_id}
        )
        if film_exists.fetchone() is None:
            raise FilmNotFound(f"Film {data.film_id} not found")

        hall_exists = await self.session.execute(
            text("SELECT 1 FROM halls WHERE id = :id"), {"id": data.hall_id}
        )
        if hall_exists.fetchone() is None:
            raise HallNotFound(f"Hall {data.hall_id} not found")

        query = text(
            """
            SELECT * FROM add_session(
                :film_id,
                :hall_id,
                :start_time,
                :price
            )
        """
        )

        try:
            result = await self.session.execute(query, data.model_dump())
            await self.session.commit()

        except DBAPIError as e:
            cause = getattr(e.orig, "__cause__", None)

            if isinstance(cause, asyncpg.exceptions.RaiseError):
                msg = str(cause).replace("ERROR:  ", "")
                raise SessionConflictError(msg)

            raise

        row = result.fetchone()
        if row is None:
            raise HTTPException(status_code=500, detail="Unknown DB error")

        return Session(**row._mapping)


def get_session_repository(session: AsyncSession = Depends(get_session)):
    return SessionRepository(session)
