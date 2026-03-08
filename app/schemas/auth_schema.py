"""
Authentication Schemas
Pydantic models for authentication requests and responses
"""

from uuid import UUID
from pydantic import BaseModel, Field, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    role_id: UUID
    full_name: str = Field(..., min_length=1)
    mobile_number: str = Field(..., min_length=10, max_length=15)


class UserAuthResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    mobile_number: str | None = None
    role_id: UUID

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserAuthResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
