from typing import Protocol

from schemas.sessions import NewSession, Session


class ISessionRepository(Protocol):

    async def add_session(self, data: NewSession) -> Session: ...
