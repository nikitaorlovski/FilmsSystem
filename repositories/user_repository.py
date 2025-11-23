from fastapi.params import Depends
from pydantic import EmailStr
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
import asyncpg
from sqlalchemy.exc import DBAPIError

from database.db import get_session
from domain.exceptions import UserAlreadyExistsError, UserValidationError
from domain.interfaces.user_repository import IUserRepository
from schemas.users import User, UserLogin


class UserRepository(IUserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(
            self, name: str, email: EmailStr, password_hash: bytes
    ) -> User:
        query = text(
            """
            SELECT * FROM create_user(:name, :email, :password_hash);
            """
        )

        values = {
            "name": name,
            "email": email,
            "password_hash": password_hash
        }

        try:
            result = await self.session.execute(query, values)
            row = result.fetchone()
            await self.session.commit()

            if not row:
                raise UserValidationError("Failed to create user")

            return User(**row._mapping)

        except DBAPIError as e:
            await self.session.rollback()
            cause = getattr(e.orig, "__cause__", None)

            if isinstance(cause, asyncpg.exceptions.RaiseError):
                msg = str(cause).replace("ERROR:  ", "")

                if "already exists" in msg.lower():
                    raise UserAlreadyExistsError(f"Пользователь с email '{email}' уже существует")
                elif "name" in msg.lower() and "required" in msg.lower():
                    raise UserValidationError("Имя пользователя обязательно")
                elif "email" in msg.lower() and "required" in msg.lower():
                    raise UserValidationError("Email обязателен")
                elif "password" in msg.lower() and "required" in msg.lower():
                    raise UserValidationError("Пароль обязателен")
                else:
                    raise UserValidationError(f"Ошибка валидации: {msg}")

            if "unique" in str(e).lower() and "email" in str(e).lower():
                raise UserAlreadyExistsError(f"Пользователь с email '{email}' уже существует")

            raise UserValidationError("Ошибка при создании пользователя")

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

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.session.execute(
            text("SELECT id, name, email, role FROM users WHERE id = :id"),
            {"id": user_id},
        )
        row = result.fetchone()
        if row is None:
            return None
        return User(**row._mapping)


async def get_user_repo(
        session: AsyncSession = Depends(get_session),
) -> IUserRepository:
    return UserRepository(session)