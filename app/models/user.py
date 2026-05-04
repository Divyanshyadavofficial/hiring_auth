from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    name:str
    age:int
    email:str
    password:str
    role: str = "candidate"

class updated_user(BaseModel):
    name:Optional[str]=None
    age:Optional[int]=None
    email:Optional[str]=None

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    age: int
    email: str

class UserCreate(BaseModel):
    name: str
    age: int
    email: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str