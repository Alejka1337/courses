from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from src.enums import UserType


class UserRegistration(BaseModel):
    name: Optional[str] = None
    surname: Optional[str] = None
    username: str
    email: str
    password: str
    phone: Optional[str] = None
    country: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    name: Optional[str] = None
    surname: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None


class UsernameUpdate(BaseModel):
    username: Optional[str] = None


class UserActivate(BaseModel):
    code: str
    username: str


class SetNewPassword(BaseModel):
    code: str
    new_pass: str
    email: str


class ResetPassword(BaseModel):
    email: str


class LoginWithGoogle(BaseModel):
    google_token: str


class BuyCourse(BaseModel):
    course_id: int


class AuthResponse(BaseModel):
    access_token: str
    access_token_expire: datetime
    user_id: int
    username: str
    user_type: UserType
    refresh_token: str
    refresh_token_expire: datetime
    message: str


class StudentCreateViaGoogle(BaseModel):
    user_id: int
    name: str
    surname: str
    email: str
    image_path: str


class StudentCreate(BaseModel):
    user_id: int
    email: str
    name: Optional[str] = None
    surname: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
