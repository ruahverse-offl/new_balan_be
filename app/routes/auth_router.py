"""
Authentication Router
FastAPI routes for authentication (login, register, token refresh, logout, password change)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from uuid import UUID
from typing import List
from app.db.db_connection import get_db
from app.services.auth_service import AuthService
from app.db.models import User, Role
from sqlalchemy import select
from app.schemas.auth_schema import (
    LoginRequest,
    RegisterRequest,
    AuthResponse,
    RefreshTokenRequest,
    TokenResponse
)
from app.utils.auth import get_current_user_id
from app.utils.rbac import get_user_permissions_dependency, RBACService
from app.utils.request_utils import get_client_ip
from app.utils.password import hash_password, verify_password

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

# In-memory token blacklist (for production, use Redis)
_blacklisted_tokens: set = set()


def is_token_blacklisted(token: str) -> bool:
    return token in _blacklisted_tokens


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)


@router.post("/login", status_code=status.HTTP_200_OK, response_model=AuthResponse)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    User login endpoint.

    Authenticates a user with email and password, returns JWT tokens.
    """
    service = AuthService(db)
    return await service.login(login_data)


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=AuthResponse)
async def register(
    register_data: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    User registration endpoint.

    Creates a new user account and returns JWT tokens.
    """
    ip_address = get_client_ip(request)
    service = AuthService(db)
    return await service.register(register_data, ip_address)


@router.post("/refresh", status_code=status.HTTP_200_OK, response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token endpoint.

    Generates a new access token using a valid refresh token.
    """
    service = AuthService(db)
    return await service.refresh_access_token(refresh_data.refresh_token)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    request: Request,
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Logout endpoint. Blacklists the current access token.
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        _blacklisted_tokens.add(token)
    return {"message": "Logged out successfully"}


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    data: ChangePasswordRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Change password for the currently authenticated user.
    Requires current password for verification.
    """
    # Get user
    stmt = select(User).where(User.id == current_user_id, User.is_deleted == False)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Verify current password
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    # Don't allow same password
    if verify_password(data.new_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password must be different from current password")

    # Update password
    user.password_hash = hash_password(data.new_password)
    await db.commit()

    return {"message": "Password changed successfully"}


@router.get("/me/permissions", response_model=dict)
async def get_my_permissions(
    permissions: List[str] = Depends(get_user_permissions_dependency),
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's permissions and role.
    """
    rbac_service = RBACService(db)
    role = await rbac_service.get_user_role(current_user_id)
    role_code = role.name if role else "CUSTOMER"
    return {"permissions": permissions, "role_code": role_code}


@router.get("/customer-role-id", status_code=status.HTTP_200_OK)
async def get_customer_role_id(
    db: AsyncSession = Depends(get_db)
):
    """
    Public endpoint to get the CUSTOMER role ID for registration.
    No authentication required.
    """
    stmt = (
        select(Role)
        .where(Role.name == "CUSTOMER")
        .where(Role.is_active == True)
        .where(Role.is_deleted == False)
    )
    result = await db.execute(stmt)
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CUSTOMER role not found"
        )
    return {"role_id": str(role.id)}
