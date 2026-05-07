from pydantic import BaseModel,EmailStr
from typing import Optional

class User(BaseModel):
    name:str
    age:int
    email:EmailStr
    password:str
    role: str = "candidate"

class updated_user(BaseModel):
    name:Optional[str]=None
    age:Optional[int]=None
    email:Optional[str]=None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    age: int
    email: EmailStr
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    name: str
    age: int
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str