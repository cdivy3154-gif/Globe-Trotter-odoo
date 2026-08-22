from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=255)
    language_pref: str = Field(default="en", max_length=10)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=128)


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255)
    language_pref: Optional[str] = Field(None, max_length=10)
    avatar_path: Optional[str] = Field(None, max_length=500)


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: str
    avatar_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str = Field(..., min_length=6, max_length=128)