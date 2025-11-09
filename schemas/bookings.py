from pydantic import BaseModel, field_validator
from datetime import datetime


class NewBooking(BaseModel):
    session_id: int
    seat_number: int

    @field_validator("seat_number")
    def validate_seat(cls, value):
        if value <= 0:
            raise ValueError("Seat number must be positive")
        return value


class Booking(BaseModel):
    id: int
    user_id: int
    session_id: int
    seat_number: int
    status: str
    created_at: datetime
