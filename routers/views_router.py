from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from database.db import get_session
from core.auth import get_current_user_id, admin_required

router = APIRouter(prefix="/views", tags=["Views"])

@router.get("/user-info")
async def get_user_info(
        user_id: int = Depends(get_current_user_id),
        session: AsyncSession = Depends(get_session),
):
    """
    Получить информацию о пользователе
    """
    try:
        query = text("SELECT * FROM vw_user_info WHERE id = :user_id")
        result = await session.execute(query, {"user_id": user_id})
        user = result.fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return dict(user._mapping)
    except Exception as e:
        print(f"Error fetching user info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/user-history")
async def get_user_history(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    """
    Получить историю бронирований пользователя из vw_user_history
    """
    try:
        query = text("""
            SELECT * FROM vw_user_history 
            WHERE user_id = :user_id 
            ORDER BY start_time DESC
        """)
        result = await session.execute(query, {"user_id": user_id})
        bookings = [dict(row._mapping) for row in result.fetchall()]
        return bookings
    except Exception as e:
        print(f"Error fetching user history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/top-films")
async def get_top_films(
    session: AsyncSession = Depends(get_session),
):
    res = await session.execute(text("SELECT * FROM vw_top_films"))
    return [dict(r._mapping) for r in res.fetchall()]

@router.get("/active-bookings", dependencies=[Depends(admin_required)])
async def get_active_bookings(
    session: AsyncSession = Depends(get_session),
):
    res = await session.execute(text("SELECT * FROM vw_active_bookings"))
    return [dict(r._mapping) for r in res.fetchall()]

@router.get("/sessions/halls")
async def get_sessions_with_halls(
    session: AsyncSession = Depends(get_session),
):
    res = await session.execute(text("SELECT * FROM vw_sessions_with_halls"))
    return [dict(r._mapping) for r in res.fetchall()]

@router.get("/upcoming-sessions/{film_id}")
async def get_upcoming_sessions_for_film(
    film_id: int,
    session: AsyncSession = Depends(get_session)
):
    """
    Получить будущие сеансы конкретного фильма
    """
    try:
        query = text("""
            SELECT *
            FROM vw_upcoming_sessions
            WHERE film_id = :film_id
            ORDER BY start_time
        """)
        rows = await session.execute(query, {"film_id": film_id})
        return [dict(r._mapping) for r in rows.fetchall()]

    except Exception as e:
        print("Error fetching upcoming film sessions:", e)
        raise HTTPException(500, "Internal server error")

@router.get("/booking-details/{booking_id}")
async def get_booking_details(
        booking_id: int,
        user_id: int = Depends(get_current_user_id),
        session: AsyncSession = Depends(get_session),
):
    """
    Получить детальную информацию о бронировании
    """
    try:
        query = text("""
            SELECT 
                b.id as booking_id,
                b.seat_number,
                b.status,
                b.created_at,
                f.title as film_title,
                f.duration,
                f.genre,
                f.description,
                f.rating,
                s.start_time,
                s.price,
                h.name as hall_name,
                h.capacity,
                u.name as user_name,
                u.email
            FROM bookings b
            JOIN sessions s ON s.id = b.session_id
            JOIN films f ON f.id = s.film_id
            JOIN halls h ON h.id = s.hall_id
            JOIN users u ON u.id = b.user_id
            WHERE b.id = :booking_id AND b.user_id = :user_id
        """)
        result = await session.execute(query, {"booking_id": booking_id, "user_id": user_id})
        booking = result.fetchone()

        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        return dict(booking._mapping)
    except Exception as e:
        print(f"Error fetching booking details: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

