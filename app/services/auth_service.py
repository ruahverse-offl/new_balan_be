"""
Authentication Service
Business logic for user authentication (login, register, token refresh)
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
import logging

from app.repositories.users_repository import UsersRepository
from app.db.models import User, Role
from app.utils.password import hash_password, verify_password
from app.utils.jwt_token import create_access_token, create_refresh_token, decode_token
from app.schemas.auth_schema import (
    LoginRequest,
    RegisterRequest,
    AuthResponse,
    UserAuthResponse,
    TokenResponse
)

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.users_repository = UsersRepository(session)
    
    async def login(self, login_data: LoginRequest) -> AuthResponse:
        """
        Authenticate user and return JWT tokens.
        
        Args:
            login_data: Login credentials (email and password)
            
        Returns:
            AuthResponse with tokens and user information
            
        Raises:
            HTTPException: 401 if credentials are invalid
        """
        logger.info(f"Login attempt for email: {login_data.email}")
        
        # Find user by email
        stmt = (
            select(User)
            .where(User.email == login_data.email)
            .where(User.is_deleted == False)
        )
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        
        # Check if user exists
        if not user:
            logger.warning(f"Login failed: User not found for email: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f"Login failed: User inactive for email: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive. Please contact administrator."
            )
        
        # Verify password
        if not verify_password(login_data.password, user.password_hash):
            logger.warning(f"Login failed: Invalid password for email: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Create tokens
        access_token = create_access_token(
            user_id=user.id,
            email=user.email,
            role_id=user.role_id
        )
        refresh_token = create_refresh_token(user_id=user.id)
        
        logger.info(f"Login successful for user: {user.id}")
        
        # Return response
        return AuthResponse(
            token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserAuthResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                mobile_number=user.mobile_number,
                role_id=user.role_id
            )
        )
    
    async def register(self, register_data: RegisterRequest, created_ip: str) -> AuthResponse:
        """
        Register a new user and return JWT tokens.
        
        Args:
            register_data: Registration data
            created_ip: IP address of the user registering
            
        Returns:
            AuthResponse with tokens and user information
            
        Raises:
            HTTPException: 
                - 409 if email already exists
                - 404 if role_id is invalid
        """
        logger.info(f"Registration attempt for email: {register_data.email}")
        
        # Check if email already exists
        stmt = select(User).where(User.email == register_data.email)
        result = await self.session.execute(stmt)
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            logger.warning(f"Registration failed: Email already exists: {register_data.email}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        # Signup always assigns CUSTOMER role so users only get customer permissions
        role_stmt = (
            select(Role)
            .where(Role.name.ilike("CUSTOMER"))
            .where(Role.is_active == True)
            .where(Role.is_deleted == False)
        )
        role_result = await self.session.execute(role_stmt)
        role = role_result.scalar_one_or_none()
        
        if not role:
            logger.error("Registration failed: CUSTOMER role not found in database")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration is not configured. Please contact support."
            )
        
        # Hash password
        password_hash = hash_password(register_data.password)
        
        # Create user data (always Customer role)
        user_data = {
            "role_id": role.id,
            "full_name": register_data.full_name,
            "mobile_number": register_data.mobile_number,
            "email": register_data.email,
            "password_hash": password_hash,
            "is_active": True
        }
        
        # Create user - use own ID as created_by after creation
        from app.db.models import User as UserModel
        import uuid as uuid_module
        new_user_id = uuid_module.uuid4()
        user_data["id"] = new_user_id
        user = await self.users_repository.create(
            user_data,
            created_by=new_user_id,
            created_ip=created_ip
        )

        # Commit transaction
        await self.session.commit()

        # Refresh user to get all fields
        await self.session.refresh(user)
        
        logger.info(f"Registration successful for user: {user.id}")
        
        # Create tokens
        access_token = create_access_token(
            user_id=user.id,
            email=user.email,
            role_id=user.role_id
        )
        refresh_token = create_refresh_token(user_id=user.id)
        
        # Return response
        return AuthResponse(
            token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserAuthResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                mobile_number=user.mobile_number,
                role_id=user.role_id
            )
        )
    
    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """
        Generate a new access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            TokenResponse with new access token and refresh token
            
        Raises:
            HTTPException: 401 if refresh token is invalid
        """
        logger.info("Token refresh attempt")
        
        # Decode refresh token
        try:
            payload = decode_token(refresh_token)
        except HTTPException:
            logger.warning("Token refresh failed: Invalid refresh token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Verify token type
        if payload.get("type") != "refresh":
            logger.warning("Token refresh failed: Not a refresh token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        # Get user ID
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_id = UUID(user_id_str)
        
        # Verify user exists and is active
        stmt = (
            select(User)
            .where(User.id == user_id)
            .where(User.is_active == True)
            .where(User.is_deleted == False)
        )
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"Token refresh failed: User not found: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new tokens
        access_token = create_access_token(
            user_id=user.id,
            email=user.email,
            role_id=user.role_id
        )
        new_refresh_token = create_refresh_token(user_id=user.id)
        
        logger.info(f"Token refresh successful for user: {user.id}")
        
        # Return response
        from app.config import get_settings
        settings = get_settings()
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
