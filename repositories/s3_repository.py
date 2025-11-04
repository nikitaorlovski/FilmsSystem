import aioboto3
from core.config import settings
from domain.interfaces.s3_repository import IS3Repository


class S3Repository(IS3Repository):
    def __init__(
        self,
        endpoint_url: str = settings.s3.endpoint_url,
        access_key: str = settings.s3.access_key,
        secret_key: str = settings.s3.secret_key,
        region: str = settings.s3.region,
        bucket_name: str = settings.s3.bucket_name,
    ):
        self.endpoint_url = endpoint_url
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self.bucket_name = bucket_name
        self.session = aioboto3.Session()

    async def _client(self):
        return self.session.client(
            "s3",
            region_name=self.region,
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )

    async def upload_file(self, image: bytes, key: str):
        async with await self._client() as s3:
            await s3.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=image,
            )
        return f"{settings.s3.public_url}/{key}"

    async def delete(self, key: str) -> None:
        async with await self._client() as s3:
            await s3.delete_object(
                Bucket=self.bucket_name,
                Key=key,
            )


def get_s3_repo():
    return S3Repository()
