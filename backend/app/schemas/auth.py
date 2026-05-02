"""Auth request/response schemas."""

import uuid

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    role: str | None = None
    type: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "event_admin"


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    # v0.50m: system-level capability flags. Added here so the frontend
    # /auth/me response can drive UI gating — without them, Staff users
    # with can_create_events couldn't see the "+ New event" button.
    can_manage_users: bool = False
    can_create_events: bool = False

    model_config = {"from_attributes": True}
