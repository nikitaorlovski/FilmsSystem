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
    try:
        query = text("SELECT * FROM vw_user_info WHERE id = :user_id")
        result = await session.execute(query, {"user_id": user_id})
        user = result.fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return dict(user._mapping)

    except Exception as e:
        print("Error fetching user info:", e)
        raise HTTPException(500, "Internal server error")

@router.get("/user-history")
async def get_user_history(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    try:
        query = text("""
            SELECT * FROM vw_user_history
            WHERE user_id = :user_id
            ORDER BY start_time DESC
        """)
        rows = await session.execute(query, {"user_id": user_id})
        return [dict(r._mapping) for r in rows.fetchall()]

    except Exception as e:
        print("Error fetching user history:", e)
        raise HTTPException(500, "Internal server error")

@router.get("/top-films")
async def get_top_films(
    session: AsyncSession = Depends(get_session),
):
    rows = await session.execute(text("SELECT * FROM vw_top_films"))
    return [dict(r._mapping) for r in rows.fetchall()]

@router.get("/top-rated")
async def get_top_rated_films(
    session: AsyncSession = Depends(get_session),
):
    rows = await session.execute(text("SELECT * FROM vw_top_rated_films"))
    return [dict(r._mapping) for r in rows.fetchall()]

@router.get("/films/upcoming")
async def get_films_with_upcoming_sessions(
    session: AsyncSession = Depends(get_session),
):
    rows = await session.execute(text("SELECT * FROM vw_films_with_upcoming_sessions"))
    return [dict(r._mapping) for r in rows.fetchall()]


@router.get("/popular-last-week")
async def get_popular_last_week(
    session: AsyncSession = Depends(get_session),
):
    rows = await session.execute(text("SELECT * FROM vw_popular_last_week"))
    return [dict(r._mapping) for r in rows.fetchall()]

@router.get("/active-bookings", dependencies=[Depends(admin_required)])
async def get_active_bookings(
    session: AsyncSession = Depends(get_session),
):
    rows = await session.execute(text("SELECT * FROM vw_active_bookings"))
    return [dict(r._mapping) for r in rows.fetchall()]

@router.get("/sessions/halls")
async def get_sessions_with_halls(
    session: AsyncSession = Depends(get_session),
):
    rows = await session.execute(text("SELECT * FROM vw_sessions_with_halls"))
    return [dict(r._mapping) for r in rows.fetchall()]

@router.get("/upcoming-sessions/{film_id}")
async def get_upcoming_sessions_for_film(
    film_id: int,
    session: AsyncSession = Depends(get_session)
):
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

        row = await session.execute(query, {"booking_id": booking_id, "user_id": user_id})
        booking = row.fetchone()

        if not booking:
            raise HTTPException(404, "Booking not found")

        return dict(booking._mapping)

    except Exception as e:
        print("Error fetching booking:", e)
        raise HTTPException(500, "Internal server error")

@router.get("/hall-usage", dependencies=[Depends(admin_required)])
async def get_hall_usage(
    session: AsyncSession = Depends(get_session),
):
    query = text("""
        SELECT hall_id, name, capacity, total_sessions
        FROM vw_hall_usage
        ORDER BY hall_id
    """)

    result = await session.execute(query)
    rows = result.fetchall()

    return [
        {
            "id": row.hall_id,
            "name": row.name,
            "capacity": row.capacity,
            "total_sessions": row.total_sessions
        }
        for row in rows
    ]
