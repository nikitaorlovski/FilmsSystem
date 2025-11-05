from pydantic import BaseModel, Field


class HallCreate(BaseModel):
    name: str
    capacity: int = Field(..., ge=1, description="Количество мест в зале")

class Hall(BaseModel):
    id: int
    name: str
    capacity: int