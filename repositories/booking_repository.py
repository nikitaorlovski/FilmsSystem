from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_session
from domain.interfaces.booking_repository import IBookingRepository
from domain.exceptions import DomainError
from schemas.bookings import Booking, NewBooking
import asyncpg
from sqlalchemy.exc import DBAPIError


class BookingRepository(IBookingRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, data: NewBooking) -> Booking:
        query = text(
            """
            SELECT *
            FROM add_booking(:user_id, :session_id, :seat_number);
        """
        )

        try:
            result = await self.session.execute(
                query,
                {
                    "user_id": user_id,
                    "session_id": data.session_id,
                    "seat_number": data.seat_number,
                },
            )
            await self.session.commit()

        except DBAPIError as e:
            cause = getattr(e.orig, "__cause__", None)

            if isinstance(cause, asyncpg.exceptions.RaiseError):
                msg = str(cause).replace("ERROR:  ", "")
                raise DomainError(msg)

            raise

        row = result.fetchone()
        return Booking(**row._mapping)

    async def get_user_bookings(self, user_id: int) -> list[Booking]:
        query = text(
            """
            SELECT id, user_id, session_id, seat_number, status, created_at
            FROM bookings
            WHERE user_id = :user_id
            ORDER BY created_at DESC;
        """
        )

        result = await self.session.execute(query, {"user_id": user_id})
        rows = result.fetchall()
        return [Booking(**row._mapping) for row in rows]

    async def cancel(self, booking_id: int, user_id: int) -> Booking:
        query = text(
            """
            SELECT *
            FROM cancel_booking(:booking_id, :user_id);
        """
        )

        try:
            result = await self.session.execute(
                query,
                {
                    "booking_id": booking_id,
                    "user_id": user_id,
                },
            )
            await self.session.commit()

        except DBAPIError as e:
            cause = getattr(e.orig, "__cause__", None)

            if isinstance(cause, asyncpg.exceptions.RaiseError):
                msg = str(cause).replace("ERROR:  ", "")
                raise DomainError(msg)

            raise

        row = result.fetchone()
        return Booking(**row._mapping)

    async def get_all(self) -> list[Booking]:
        query = text(
            """
            SELECT id, user_id, session_id, seat_number, status, created_at
            FROM bookings
            ORDER BY created_at DESC
        """
        )
        result = await self.session.execute(query)
        rows = result.fetchall()
        return [Booking(**row._mapping) for row in rows]


async def get_booking_repo(
    session: AsyncSession = Depends(get_session),
) -> BookingRepository:
    return BookingRepository(session)
