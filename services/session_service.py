from fastapi import Depends

from domain.exceptions import SessionNotFoundError, SessionHasActiveBookingsError, SessionConflictError
from domain.interfaces.session_repository import ISessionRepository
from repositories.session_repository import SessionRepository, get_session_repository
from schemas.sessions import NewSession, Session


class SessionService:
    def __init__(self, repository: ISessionRepository):
        self.repository = repository

    async def add(self, data: NewSession) -> Session:
        return await self.repository.add_session(data)

    async def get_all(self) -> list[Session]:
        return await self.repository.get_all_sessions()

    async def delete(self, session_id: int) -> None:
        try:
            return await self.repository.delete_session(session_id)
        except (SessionNotFoundError, SessionHasActiveBookingsError, SessionConflictError) as e:
            raise e
        except Exception as e:
            raise SessionConflictError(f"Failed to delete session: {str(e)}")


def get_session_service(repo: SessionRepository = Depends(get_session_repository)):
    return SessionService(repo)
