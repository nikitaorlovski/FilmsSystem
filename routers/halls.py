from fastapi import APIRouter, Depends, HTTPException

from core.auth import admin_required
from domain.exceptions import HallNotFound, HallValidationError, HallAlreadyExistsError, HallHasFutureSessionsError
from repositories.hall_repository import HallRepository, get_hall_repository
from schemas.halls import HallCreate, Hall

router = APIRouter(prefix="/halls", tags=["Halls"])


@router.post("/", response_model=Hall, dependencies=[Depends(admin_required)])
async def add_hall(
        hall: HallCreate, repository: HallRepository = Depends(get_hall_repository)
) -> Hall:
    try:
        return await repository.add_hall(hall)

    except HallAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))

    except HallValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=list[Hall])
async def get_halls(
        repository: HallRepository = Depends(get_hall_repository),
) -> list[Hall]:
    return await repository.get_all_halls()


@router.delete("/{id}", status_code=204, dependencies=[Depends(admin_required)])
async def delete_hall(
        id: int, repository: HallRepository = Depends(get_hall_repository)
):
    try:
        return await repository.delete_hall(id)

    except HallNotFound:
        raise HTTPException(status_code=404, detail="Hall not found")

    except HallHasFutureSessionsError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except HallValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))