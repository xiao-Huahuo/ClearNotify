from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel

from app.models.user import UserBase


class UserCreate(UserBase):
    pwd: str


class UserRead(UserBase):
    uid: int
    created_time: datetime
    last_login: datetime
    is_admin: bool = False
    email_verified: bool = False


class UserRegisterResponse(SQLModel):
    user: UserRead
    verification_required: bool = True
    delivery_channel: str = "email"
    preview_code: Optional[str] = None


class EmailVerificationRequest(SQLModel):
    email: str
    code: str


class EmailVerificationResendRequest(SQLModel):
    email: str


class UserUpdate(SQLModel):
    uname: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    pwd: Optional[str] = None
    avatar_url: Optional[str] = None
