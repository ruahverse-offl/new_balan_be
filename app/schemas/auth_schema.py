"""
Authentication Schemas
Pydantic models for authentication requests and responses
"""

from uuid import UUID
from pydantic import BaseModel, Field, EmailStr, field_validator

from app.utils.password_policy import assert_password_meets_policy


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1)
    mobile_number: str = Field(..., min_length=10, max_length=15)
    # role_id is ignored: signup assigns PUBLIC (preferred) or legacy CUSTOMER — end-customer roles for logged-in checkout

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        assert_password_meets_policy(v)
        return v.strip()


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_new_password_strength(cls, v: str) -> str:
        assert_password_meets_policy(v)
        return v.strip()


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
