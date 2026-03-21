"""
RBAC (Role-Based Access Control) Utilities
Permission checking dependencies and service for FastAPI
"""

from typing import Any, Callable, Dict, List, Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.db_connection import get_db
from app.db.models import User, Role, Permission, RolePermission, MenuTask, RoleTaskGrant
from app.utils.auth import get_current_user_id


class RBACService:
    """Service for role-based access control operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_role(self, user_id: UUID) -> Optional[Role]:
        """Get the Role object for a user."""
        stmt = (
            select(Role)
            .join(User, User.role_id == Role.id)
            .where(User.id == user_id)
            .where(User.is_deleted == False)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def has_permission(self, user_id: UUID, permission_code: str) -> bool:
        """Check if a user's role has the given permission code."""
        stmt = (
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(User, User.role_id == RolePermission.role_id)
            .where(User.id == user_id)
            .where(User.is_deleted == False)
            .where(Permission.code == permission_code)
            .where(Permission.is_deleted == False)
            .where(RolePermission.is_deleted == False)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_user_permissions(self, user_id: UUID) -> List[str]:
        """Get all permission codes for a user's role."""
        stmt = (
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(User, User.role_id == RolePermission.role_id)
            .where(User.id == user_id)
            .where(User.is_deleted == False)
            .where(Permission.is_deleted == False)
            .where(RolePermission.is_deleted == False)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_sidebar_menu_items(self, user_id: UUID) -> List[Dict[str, Any]]:
        """
        Return menu tasks visible in the admin sidebar for this user.

        Rows come from ``role_task_grants`` joined to ``menu_tasks`` for the user's role.
        Included only when ``show_in_menu`` and ``can_read`` are true and rows are not deleted.

        Returns:
            List of dicts with keys: code, display_name, sort_order, icon_key (optional).
        """
        stmt = (
            select(
                MenuTask.code,
                MenuTask.display_name,
                MenuTask.sort_order,
                MenuTask.icon_key,
            )
            .join(RoleTaskGrant, RoleTaskGrant.menu_task_id == MenuTask.id)
            .join(User, User.role_id == RoleTaskGrant.role_id)
            .where(User.id == user_id)
            .where(User.is_deleted == False)
            .where(MenuTask.is_deleted == False)
            .where(MenuTask.is_active == True)
            .where(RoleTaskGrant.is_deleted == False)
            .where(RoleTaskGrant.show_in_menu == True)
            .where(RoleTaskGrant.can_read == True)
            .order_by(MenuTask.sort_order.asc(), MenuTask.display_name.asc())
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        return [
            {
                "code": r.code,
                "display_name": r.display_name,
                "sort_order": r.sort_order,
                "icon_key": r.icon_key,
            }
            for r in rows
        ]


def require_permission(permission_code: str) -> Callable:
    """
    FastAPI dependency factory that checks if the current user has a specific permission.

    Returns the user's UUID if authorized, raises 403 if not.
    """
    async def permission_dependency(
        current_user_id: UUID = Depends(get_current_user_id),
        db: AsyncSession = Depends(get_db)
    ) -> UUID:
        rbac_service = RBACService(db)
        has_perm = await rbac_service.has_permission(current_user_id, permission_code)
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission_code} required"
            )
        return current_user_id

    return permission_dependency


def require_any_permission(permission_codes: List[str]) -> Callable:
    """
    FastAPI dependency factory that checks if the current user has at least one of the given permissions.

    Returns the user's UUID if authorized, raises 403 if not.
    """
    async def permission_dependency(
        current_user_id: UUID = Depends(get_current_user_id),
        db: AsyncSession = Depends(get_db)
    ) -> UUID:
        rbac_service = RBACService(db)
        for code in permission_codes:
            if await rbac_service.has_permission(current_user_id, code):
                return current_user_id
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: one of {permission_codes} required"
        )
    return permission_dependency


async def get_user_permissions_dependency(
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> List[str]:
    """FastAPI dependency that returns a list of permission codes for the current user."""
    rbac_service = RBACService(db)
    return await rbac_service.get_user_permissions(current_user_id)
