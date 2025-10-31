from fastapi.params import Depends
from pydantic import EmailStr

from core.security import hash_password, create_jwt, verify_password
from core.config import settings
from domain.exceptions import InvalidCredentialsError
from repositories.user_repository import UserRepository, get_user_repo
from schemas.token import Token
from schemas.users import UserRegistration


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def registration(self, userdata: UserRegistration) -> Token:
        hashed_password = hash_password(userdata.password)

        user = await self.repository.create_user(
            name=userdata.name,
            email=userdata.email,
            password_hash=hashed_password,
        )

        access_token = create_jwt(
            token_type="access",
            token_data=str(user.id),
            expire_minutes=settings.auth_jwt.access_token_expire,
        )
        return Token(access_token=access_token)

    async def login(self, email: EmailStr, password: str) -> Token:
        user = await self.repository.get_by_email(email)
        if not user:
            raise InvalidCredentialsError

        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError

        access_token = create_jwt(
            token_type="access",
            token_data=str(user.id),
            expire_minutes=settings.auth_jwt.access_token_expire,
        )

        return Token(access_token=access_token)


async def get_user_service(
    repo: UserRepository = Depends(get_user_repo),
) -> UserService:
    return UserService(repo)
