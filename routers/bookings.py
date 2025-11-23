from fastapi import APIRouter, Depends
from schemas.bookings import Booking, NewBooking, BookingDetailed
from services.booking_service import BookingService, get_booking_service
from core.auth import get_current_user_id, admin_required
from domain.exceptions import DomainError
from fastapi import HTTPException

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("/", response_model=Booking)
async def create_booking(
    data: NewBooking,
    user_id: int = Depends(get_current_user_id),
    service: BookingService = Depends(get_booking_service),
):
    try:
        return await service.create(user_id, data)
    except DomainError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/me", response_model=list[BookingDetailed])
async def get_my_bookings(
    user_id: int = Depends(get_current_user_id),
    service: BookingService = Depends(get_booking_service),
):
    return await service.get_my(user_id)


@router.put("/{booking_id}/cancel", response_model=Booking)
async def cancel_booking(
    booking_id: int,
    user_id: int = Depends(get_current_user_id),
    service: BookingService = Depends(get_booking_service),
):
    try:
        return await service.cancel(booking_id, user_id)
    except DomainError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/", response_model=list[Booking], dependencies=[Depends(admin_required)])
async def get_all_bookings(
    service: BookingService = Depends(get_booking_service),
):
    return await service.get_all()

@router.get("/{id}/bookings")
async def get_session_bookings(
    id: int,
    service: BookingService = Depends(get_booking_service)
):
    try:
        all_bookings = await service.get_all()
        session_bookings = [booking for booking in all_bookings if booking.session_id == id]
        return session_bookings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))