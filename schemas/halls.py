from pydantic import BaseModel

class HallCreate(BaseModel):
    name: str
    capacity: int

class Hall(BaseModel):
    id: int
    name: str
    capacity: int