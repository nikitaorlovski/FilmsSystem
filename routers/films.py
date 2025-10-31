from fastapi import APIRouter

router = APIRouter()

@router.get("/films")
async def get_films():
    return []