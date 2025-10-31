from fastapi.params import Depends
from pydantic import EmailStr
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from database.db import get_session
from domain.exceptions import UserAlreadyExistsError
from schemas.users import User, UserLogin


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(
        self, name: str, email: EmailStr, password_hash: bytes
    ) -> User:
        query = text(
            """
            INSERT INTO users (name, email, password_hash, role)
            VALUES (:name, :email, :password_hash, 'user')
            RETURNING id, name, email, role
        """
        )

        try:
            result = await self.session.execute(
                query, {"name": name, "email": email, "password_hash": password_hash}
            )
            row = result.fetchone()
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise UserAlreadyExistsError

        return User(**row._mapping)

    async def get_by_email(self, email: EmailStr) -> UserLogin | None:
        query = text(
            """
            SELECT id, name, email, password_hash, role
            FROM users
            WHERE email = :email
            LIMIT 1
        """
        )

        result = await self.session.execute(query, {"email": email})
        row = result.fetchone()

        return UserLogin(**row._mapping) if row else None


async def get_user_repo(
    session: AsyncSession = Depends(get_session),
) -> UserRepository:
    return UserRepository(session)
