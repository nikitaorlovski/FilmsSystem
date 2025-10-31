from fastapi import APIRouter, Depends, Form, HTTPException
from pydantic import EmailStr
from domain.exceptions import InvalidCredentialsError, UserAlreadyExistsError
from schemas.token import Token
from schemas.users import UserRegistration
from services.user_service import UserService, get_user_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/registration", response_model=Token)
async def registration(
    userdata: UserRegistration,
    service: UserService = Depends(get_user_service),
):
    try:
        return await service.registration(userdata)
    except UserAlreadyExistsError:
        raise HTTPException(status_code=409, detail="User already exists")


@router.post("/login", response_model=Token)
async def login(
    email: EmailStr = Form(...),
    password: str = Form(...),
    service: UserService = Depends(get_user_service),
):
    try:
        return await service.login(email, password)
    except InvalidCredentialsError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
