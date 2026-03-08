"""
Users Service
Business logic layer for users
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
import logging

from app.repositories.users_repository import UsersRepository
from app.schemas.users_schema import (
    UserCreateRequest,
    UserUpdateRequest,
    UserResponse,
    UserListResponse
)
from app.schemas.common import PaginationResponse
from app.services.base_service import BaseService
from app.utils.password import hash_password

logger = logging.getLogger(__name__)


class UsersService(BaseService):
    """Service for users operations."""
    
    def __init__(self, session: AsyncSession):
        repository = UsersRepository(session)
        super().__init__(repository, session)
    
    async def create_user(
        self,
        data: UserCreateRequest,
        created_by: UUID,
        created_ip: str
    ) -> UserResponse:
        """Create a new user."""
        logger.info(f"Creating user: {data.email}")
        user_data = data.model_dump()
        if user_data.get("password"):
            user_data["password_hash"] = hash_password(user_data.pop("password"))
        elif not user_data.get("password_hash"):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Either password or password_hash is required")
        user_data.pop("password", None)
        # Automatically set is_active to True
        user_data["is_active"] = True
        user = await self.repository.create(user_data, created_by, created_ip)
        user_dict = self._model_to_dict(user)
        return UserResponse(**user_dict)
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[UserResponse]:
        """Get user by ID."""
        user = await self.repository.get_by_id(user_id)
        if not user:
            return None
        user_dict = self._model_to_dict(user)
        return UserResponse(**user_dict)
    
    async def get_users_list(
        self,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None
    ) -> UserListResponse:
        """Get list of users with pagination, search, and sort."""
        users, pagination = await self.repository.get_list(
            limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order
        )
        user_responses = [
            UserResponse(**self._model_to_dict(u)) for u in users
        ]
        return UserListResponse(
            items=user_responses,
            pagination=PaginationResponse(**pagination)
        )
    
    async def update_user(
        self,
        user_id: UUID,
        data: UserUpdateRequest,
        updated_by: UUID,
        updated_ip: str
    ) -> Optional[UserResponse]:
        """Update a user."""
        logger.info(f"Updating user: {user_id}")
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if update_data.get("password"):
            update_data["password_hash"] = hash_password(update_data.pop("password"))
        update_data.pop("password", None)
        user = await self.repository.update(user_id, update_data, updated_by, updated_ip)
        if not user:
            return None
        user_dict = self._model_to_dict(user)
        return UserResponse(**user_dict)
    
    async def delete_user(
        self,
        user_id: UUID,
        updated_by: UUID,
        updated_ip: str
    ) -> bool:
        """Soft delete a user."""
        logger.info(f"Deleting user: {user_id}")
        return await self.repository.soft_delete(user_id, updated_by, updated_ip)
