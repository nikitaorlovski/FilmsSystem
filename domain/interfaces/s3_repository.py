from typing import Protocol


class IS3Repository(Protocol):

    async def upload_file(self, image: bytes, key: str): ...

    async def delete(self, key: str) -> None: ...
