from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import asyncpg
from sqlalchemy.exc import DBAPIError

from domain.exceptions import HallNotFound, HallValidationError, HallAlreadyExistsError, HallHasFutureSessionsError
from domain.interfaces.hall_repository import IHallRepository
from database.db import get_session
from schemas.halls import HallCreate, Hall


class HallRepository(IHallRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_hall(self, hall: HallCreate) -> Hall:
        query = text(
            """
            SELECT * FROM add_hall(:name, :capacity);
            """
        )

        values = {
            "name": hall.name,
            "capacity": hall.capacity
        }

        try:
            result = await self.session.execute(query, values)
            row = result.fetchone()
            await self.session.commit()

            if not row:
                raise HallValidationError("Failed to create hall")

            return Hall(**row._mapping)

        except DBAPIError as e:
            await self.session.rollback()
            cause = getattr(e.orig, "__cause__", None)

            if isinstance(cause, asyncpg.exceptions.RaiseError):
                msg = str(cause).replace("ERROR:  ", "")

                if "already exists" in msg.lower():
                    raise HallAlreadyExistsError(f"Зал с названием '{hall.name}' уже существует")
                elif "capacity" in msg.lower() and "positive" in msg.lower():
                    raise HallValidationError("Вместимость зала должна быть положительной")
                elif "name" in msg.lower() and "required" in msg.lower():
                    raise HallValidationError("Название зала обязательно")
                else:
                    raise HallValidationError(f"Ошибка валидации: {msg}")

            raise HallValidationError("Ошибка при создании зала")

    async def get_all_halls(self) -> list[Hall]:
        query = text(
            """
            SELECT id, name, capacity
            FROM halls
            ORDER BY name
            """
        )

        result = await self.session.execute(query)
        rows = result.fetchall()

        return [Hall(**row._mapping) for row in rows]

    async def delete_hall(self, id: int) -> None:
        query = text("SELECT delete_hall(:hall_id);")

        try:
            await self.session.execute(
                query,
                {"hall_id": id}
            )
            await self.session.commit()

        except DBAPIError as e:
            await self.session.rollback()
            cause = getattr(e.orig, "__cause__", None)

            if isinstance(cause, asyncpg.exceptions.RaiseError):
                msg = str(cause).replace("ERROR:  ", "")

                if "not found" in msg.lower():
                    raise HallNotFound(f"Hall {id} not found")
                elif "future sessions" in msg.lower():
                    raise HallHasFutureSessionsError("Нельзя удалить зал с будущими сеансами")
                else:
                    raise HallValidationError(f"Ошибка при удалении зала: {msg}")

            raise HallValidationError("Ошибка при удалении зала")


async def get_hall_repository(session: AsyncSession = Depends(get_session)):
    return HallRepository(session)