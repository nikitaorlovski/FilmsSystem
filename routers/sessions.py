from fastapi import APIRouter, Depends, HTTPException

from core.auth import admin_required
from domain.exceptions import FilmNotFound, HallNotFound, SessionConflictError
from services.session_service import SessionService, get_session_service
from schemas.sessions import NewSession, Session

router = APIRouter(tags=["Sessions"])


@router.post(
    "/sessions/", response_model=Session, dependencies=[Depends(admin_required)]
)
async def add_session(
    new_session: NewSession,
    service: SessionService = Depends(get_session_service),
):
    try:
        return await service.add(new_session)

    except FilmNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))

    except HallNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))

    except SessionConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
