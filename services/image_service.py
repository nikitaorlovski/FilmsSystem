from fastapi import UploadFile, Depends

from domain.interfaces.s3_repository import IS3Repository
from repositories.s3_repository import get_s3_repo
from utils.image_utils import validate_image
import uuid


class ImageService:
    def __init__(self, repo: IS3Repository):
        self.repo = repo

    async def upload(self, file: UploadFile):
        contents = await validate_image(file)
        ext = file.filename.split(".")[-1]
        key = f"{uuid.uuid4()}.{ext}"
        return await self.repo.upload_file(contents, key)

    async def delete(self, image_url: str):
        key = image_url.split("/")[-1]
        await self.repo.delete(key)


def get_image_service(s3_repo: IS3Repository = Depends(get_s3_repo)):
    return ImageService(s3_repo)
