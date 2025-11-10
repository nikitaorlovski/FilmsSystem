from fastapi import APIRouter, Depends
from starlette.exceptions import HTTPException

from core.auth import admin_required
from domain.exceptions import HallNotFound
from repositories.hall_repository import HallRepository, get_hall_repository
from schemas.halls import HallCreate, Hall

router = APIRouter(prefix="/halls", tags=["Halls"])


@router.post("/", response_model=Hall, dependencies=[Depends(admin_required)])
async def add_hall(
    hall: HallCreate, repository: HallRepository = Depends(get_hall_repository)
) -> Hall:
    return await repository.add_hall(hall)


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
