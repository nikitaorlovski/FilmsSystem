from fastapi import Depends
from repositories.session_repository import SessionRepository, get_session_repository


class SessionService:
    def __init__(self, repo):
        self.repo = repo

    async def add(self, data):
        return await self.repo.add_session(data)


def get_session_service(repo: SessionRepository = Depends(get_session_repository)):
    return SessionService(repo)
