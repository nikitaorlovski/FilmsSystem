from domain.exceptions import SessionConflictError, SessionNotFoundError, SessionHasActiveBookingsError
from fastapi import Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import DBAPIError
import asyncpg
from domain.exceptions import FilmNotFound, HallNotFound
from database.db import get_session
from domain.interfaces.session_repository import ISessionRepository
from schemas.sessions import Session, NewSession


class SessionRepository(ISessionRepository):
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

    async def get_all_sessions(self) -> list[Session]:
        query = text("SELECT * FROM sessions ORDER BY start_time DESC")
        result = await self.session.execute(query)
        return [Session(**row._mapping) for row in result.fetchall()]

    async def delete_session(self, session_id: int) -> None:
        query = text("SELECT delete_session(:session_id);")

        try:
            await self.session.execute(
                query,
                {"session_id": session_id}
            )
            await self.session.commit()

        except DBAPIError as e:
            cause = getattr(e.orig, "__cause__", None)

            if isinstance(cause, asyncpg.exceptions.RaiseError):
                msg = str(cause).replace("ERROR:  ", "")

                if "not found" in msg.lower():
                    raise SessionNotFoundError(msg)
                elif "active bookings" in msg.lower():
                    raise SessionHasActiveBookingsError(msg)
                else:
                    raise SessionConflictError(msg)

            raise


def get_session_repository(session: AsyncSession = Depends(get_session)):
    return SessionRepository(session)
