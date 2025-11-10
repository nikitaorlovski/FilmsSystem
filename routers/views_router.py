from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from database.db import get_session
from core.auth import admin_required

router = APIRouter(prefix="/views", tags=["Views"])

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

