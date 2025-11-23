from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]


class AuthJWT(BaseModel):
    private_key_path: Path = ROOT / "private.pem"
    public_key_path: Path = ROOT / "public.pem"
    access_token_expire: int = 300
    refresh_token_expire_days: int = 7


class S3Settings(BaseModel):
    endpoint_url: str
    public_url: str
    access_key: str
    secret_key: str
    account_id: str
    bucket_name: str
    region: str = "auto"


class Settings(BaseSettings):
    ALGORITHM: str
    auth_jwt: AuthJWT = AuthJWT()
    s3: S3Settings

    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )


settings = Settings()
