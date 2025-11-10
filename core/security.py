import datetime
import bcrypt
import jwt

from core.config import settings


def hash_password(password: str) -> bytes:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode(), salt)
    return hashed_password


def verify_password(password: str, hashed_password: bytes) -> bool:
    return bcrypt.checkpw(password.encode(), hashed_password)


def create_jwt(
    token_type: str,
    token_data: str,
    expire_minutes: int,
) -> str:
    jwt_payload = {"type": token_type, "sub": token_data}
    return encode_jwt(payload=jwt_payload, expire_minutes=expire_minutes)


def encode_jwt(
    payload: dict,
    private_key: str = settings.auth_jwt.private_key_path.read_text(),
    algorithm: str = settings.ALGORITHM,
    expire_minutes: int = settings.auth_jwt.access_token_expire,
) -> str:
    to_encode = payload.copy()
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    expire = now + datetime.timedelta(minutes=expire_minutes)
    to_encode.update(exp=expire, iat=now)
    encoded = jwt.encode(to_encode, private_key, algorithm)
    return encoded


def decode_jwt(
    token: str,
    public_key: str = settings.auth_jwt.public_key_path.read_text(),
    algorithm: str = settings.ALGORITHM,
) -> dict:
    return jwt.decode(token, public_key, algorithms=[algorithm])
