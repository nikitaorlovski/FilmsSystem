from typing import Protocol

from pydantic import EmailStr

from schemas.users import User, UserLogin


class IUserRepository(Protocol):

    async def create_user(
        self, name: str, email: EmailStr, password_hash: bytes
    ) -> User: ...
    async def get_by_email(self, email: EmailStr) -> UserLogin | None: ...
    async def delete_user(self, id: int) -> User: ...
