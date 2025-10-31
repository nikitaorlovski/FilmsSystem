from pydantic import BaseModel, EmailStr


class UserRegistration(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    id: int
    name: str
    email: EmailStr
    password_hash: bytes
    role: str

class User(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str