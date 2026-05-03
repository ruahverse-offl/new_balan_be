"""
Users Service
Business logic layer for users
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from fastapi import HTTPException, status
import logging

from app.repositories.users_repository import UsersRepository
from app.db.models import User, Order, AppModule, ModuleRolePermission, Role
from app.domain import order_lifecycle as lc
from app.schemas.users_schema import (
    UserCreateRequest,
    UserUpdateRequest,
    UserResponse,
    UserListResponse,
    DeliveryAgentOption,
    DeliveryAgentListResponse,
)
from app.schemas.common import PaginationResponse
from app.services.base_service import BaseService
from app.utils.password import hash_password, verify_password

logger = logging.getLogger(__name__)

NIL_UUID = UUID("00000000-0000-0000-0000-000000000000")
_PROFILE_FIELDS_REQUIRING_PASSWORD = frozenset({"full_name", "email", "mobile_number"})


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
    
    async def list_delivery_agents_for_assignment(self) -> DeliveryAgentListResponse:
        """
        Return active users whose role can update the ``delivery-orders`` module
        (legacy: DELIVERY_ORDER_UPDATE), with a short workload summary for assignment UI.
        """
        stmt = (
            select(User.id, User.full_name, User.mobile_number)
            .join(ModuleRolePermission, ModuleRolePermission.role_id == User.role_id)
            .join(AppModule, AppModule.id == ModuleRolePermission.module_id)
            .join(Role, Role.id == User.role_id)
            .where(
                User.is_deleted == False,  # noqa: E712
                User.is_active == True,
                Role.is_deleted == False,  # noqa: E712
                Role.is_active == True,  # noqa: E712
                Role.name == "DELIVERY_AGENT",
                ModuleRolePermission.is_deleted == False,  # noqa: E712
                ModuleRolePermission.can_update == True,  # noqa: E712
                AppModule.is_deleted == False,  # noqa: E712
                AppModule.name == "delivery-orders",
            )
            .distinct()
            .order_by(User.full_name.asc())
        )
        rows = (await self.session.execute(stmt)).all()
        if not rows:
            return DeliveryAgentListResponse(items=[])

        agent_ids = [r[0] for r in rows]
        active_statuses = (
            lc.DELIVERY_ASSIGNED,
            lc.PARCEL_TAKEN,
            lc.OUT_FOR_DELIVERY,
        )
        cnt_stmt = (
            select(Order.delivery_assigned_user_id, func.count().label("c"))
            .where(
                Order.delivery_assigned_user_id.in_(agent_ids),
                Order.is_deleted == False,  # noqa: E712
                Order.order_status.in_(active_statuses),
            )
            .group_by(Order.delivery_assigned_user_id)
        )
        count_rows = (await self.session.execute(cnt_stmt)).all()
        counts = {row[0]: int(row[1] or 0) for row in count_rows}

        items: List[DeliveryAgentOption] = []
        for uid, full_name, mobile in rows:
            n = counts.get(uid, 0)
            if n <= 0:
                status_txt = "Available"
            elif n == 1:
                status_txt = "On active delivery (1 order)"
            else:
                status_txt = f"On active delivery ({n} orders)"
            items.append(
                DeliveryAgentOption(
                    id=uid,
                    full_name=full_name or "—",
                    mobile_number=mobile or "—",
                    delivery_status=status_txt,
                    active_delivery_count=n,
                )
            )
        return DeliveryAgentListResponse(items=items)

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
        raw = data.model_dump(exclude_unset=True)
        current_password = raw.pop("current_password", None)
        update_data = {k: v for k, v in raw.items() if v is not None}

        touches_profile = bool(_PROFILE_FIELDS_REQUIRING_PASSWORD.intersection(update_data.keys()))
        is_self = (
            updated_by is not None
            and updated_by != NIL_UUID
            and user_id == updated_by
        )
        if is_self and touches_profile:
            pw = (current_password or "").strip()
            if not pw:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is required to update your profile.",
                )
            target = await self.repository.get_by_id(user_id)
            if not target or not target.password_hash:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unable to verify account password.",
                )
            if not verify_password(pw, target.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect.",
                )

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
