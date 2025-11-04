from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from domain.exceptions import HallNotFound
from domain.interfaces.hall_repository import IHallRepository
from database.db import get_session
from schemas.halls import HallCreate, Hall


class HallRepository(IHallRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_hall(self, hall: HallCreate) -> Hall:
        hall = await self.session.execute(
            text(
                """
            INSERT INTO halls (name, capacity)
            VALUES (:name, :capacity)
            RETURNING id, name, capacity
        """
            ),
            {"name": hall.name, "capacity": hall.capacity},
        )
        row = hall.fetchone()
        await self.session.commit()
        return Hall(**row._mapping)

    async def get_all_halls(self) -> list[Hall]:
        query = text(
            """
            SELECT id, name, capacity
            FROM halls
        """
        )

        result = await self.session.execute(query)
        rows = result.fetchall()

        return [Hall(**row._mapping) for row in rows]

    async def delete_hall(self, id: int) -> None:
        result = await self.session.execute(
            text("SELECT id FROM halls WHERE id = :id"),
            {"id": id},
        )
        row = result.fetchone()

        if row is None:
            raise HallNotFound()

        await self.session.execute(
            text("DELETE FROM halls WHERE id = :id"),
            {"id": id},
        )
        await self.session.commit()


async def get_hall_repository(session: AsyncSession = Depends(get_session)):
    return HallRepository(session)
