from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from core.security import decode_jwt

security = HTTPBearer()


async def get_current_user_id(token: str = Depends(security)) -> int:
    try:
        payload = decode_jwt(token.credentials)
        return int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
