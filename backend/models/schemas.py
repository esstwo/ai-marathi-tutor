from pydantic import BaseModel, EmailStr


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class ChildCreateRequest(BaseModel):
    name: str
    age: int
    avatar: str = "🐘"
