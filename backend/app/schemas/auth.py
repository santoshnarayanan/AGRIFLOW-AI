"""Authentication API schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from app.core.enums import PlatformRole


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


class PlatformUserResponse(BaseModel):
    id: uuid.UUID
    email: str
    role: PlatformRole
    is_active: bool
