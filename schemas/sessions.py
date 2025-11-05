from pydantic import BaseModel, field_validator
from datetime import datetime, timezone

class NewSession(BaseModel):
    film_id: int
    hall_id: int
    start_time: datetime
    price: float

    @field_validator("start_time", mode="before")
    def ensure_utc(cls, v):
        if isinstance(v, datetime):
            if v.tzinfo is None:
                return v.replace(tzinfo=timezone.utc)
            return v.astimezone(timezone.utc)
        return v


class Session(BaseModel):
    id: int
    film_id: int
    hall_id: int
    start_time: datetime
    price: float
    total_seats: int
    available_seats: int
    created_at: datetime

    @field_validator("start_time", "created_at", mode="before")
    def ensure_utc(cls, v):
        if isinstance(v, datetime):
            if v.tzinfo is None:
                return v.replace(tzinfo=timezone.utc)
            return v.astimezone(timezone.utc)
        return v

