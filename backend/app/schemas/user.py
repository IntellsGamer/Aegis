"""User-related schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: str | None = None


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    is_verified: bool
    is_admin: bool
    role: str
    avatar: str | None = None
    theme: str
    high_contrast: bool
    locale: str
    created_at: datetime
    last_login: datetime | None = None


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=128)
    locale: str | None = None
    theme: str | None = None
    high_contrast: bool | None = None
    avatar: str | None = None


class UserSettingsUpdate(BaseModel):
    notify_email: bool | None = None
    notify_push: bool | None = None
    notify_threats: bool | None = None
    save_history: bool | None = None
    anonymous_reports: bool | None = None
    language: str | None = None


class UserSettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    notify_email: bool
    notify_push: bool
    notify_threats: bool
    save_history: bool
    anonymous_reports: bool
    language: str


class PublicUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str | None
    avatar: str | None


class AdminUserUpdate(BaseModel):
    is_active: bool | None = None
    is_admin: bool | None = None
    role: str | None = None
    is_verified: bool | None = None
