from fastapi import Depends

from schemas.bookings import NewBooking, Booking, BookingDetailed
from domain.interfaces.booking_repository import IBookingRepository
from repositories.booking_repository import get_booking_repo, BookingRepository


class BookingService:
    def __init__(self, repo: IBookingRepository):
        self.repo = repo

    async def create(self, user_id: int, data: NewBooking) -> Booking:
        return await self.repo.create(user_id, data)

    async def get_my(self, user_id: int) -> list[BookingDetailed]:
        return await self.repo.get_user_bookings(user_id)

    async def cancel(self, booking_id: int, user_id: int) -> Booking:
        return await self.repo.cancel(booking_id, user_id)

    async def get_all(self) -> list[Booking]:
        return await self.repo.get_all()


def get_booking_service(
    repo: BookingRepository = Depends(get_booking_repo),
) -> BookingService:
    return BookingService(repo)