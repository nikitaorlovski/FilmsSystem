from typing import Protocol

from schemas.sessions import NewSession, Session


class ISessionRepository(Protocol):

    async def add_session(self, data: NewSession) -> Session: ...
    async def get_all_sessions(self) -> list[Session]:
        ...

    async def delete_session(self, session_id: int) -> None:
        ...
