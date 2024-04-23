from typing import Optional

from pydantic import BaseModel


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
