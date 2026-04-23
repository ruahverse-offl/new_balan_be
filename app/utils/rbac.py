"""
RBAC — ``M_modules`` + ``M_module_role_permissions`` (see ``ACCESS_AND_ROLES.md``).

Route guards use :func:`require_module_action` (module + CRUD) against the matrix.
The SPA uses ``menuItems[].grants`` from ``GET /api/v1/auth/me/permissions`` (no
separate string permission list).
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Literal, Optional, Set, Tuple
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.db.models import AppModule, ModuleRolePermission, Role, User
from app.utils.auth import get_current_user_id

logger = logging.getLogger(__name__)

# CRUD action for :meth:`RBACService.has_module_action` / :func:`require_module_action`.
Action = Literal["read", "create", "update", "delete"]


class RBACService:
    """Role-based access: ``M_modules`` + ``M_module_role_permissions``."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_role(self, user_id: UUID) -> Optional[Role]:
        stmt = (
            select(Role)
            .join(User, User.role_id == Role.id)
            .where(User.id == user_id)
            .where(User.is_deleted == False)  # noqa: E712
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def has_module_action(self, user_id: UUID, module_name: str, action: Action) -> bool:
        """
        Authoritative matrix check: resolve the user's ``role_id`` from ``M_users``,
        load the row in ``M_module_role_permissions`` for that ``role_id`` and the
        ``M_modules`` row where ``name == module_name``, then allow the request only
        if the flag for the action is true: ``create`` → ``can_create``, ``read`` →
        ``can_read``, ``update`` → ``can_update``, ``delete`` → ``can_delete``.

        If there is no matrix row, or the row or module is inactive, returns ``False``.
        """
        stmt = (
            select(
                ModuleRolePermission.can_create,
                ModuleRolePermission.can_read,
                ModuleRolePermission.can_update,
                ModuleRolePermission.can_delete,
            )
            .select_from(ModuleRolePermission)
            .join(User, User.role_id == ModuleRolePermission.role_id)
            .join(AppModule, AppModule.id == ModuleRolePermission.module_id)
            .join(Role, Role.id == User.role_id)
            .where(
                User.id == user_id,
                User.is_deleted == False,  # noqa: E712
                User.is_active == True,  # noqa: E712
                Role.is_deleted == False,  # noqa: E712
                Role.is_active == True,  # noqa: E712
                AppModule.name == module_name,
                AppModule.is_deleted == False,  # noqa: E712
                AppModule.is_active == True,  # noqa: E712
                ModuleRolePermission.is_deleted == False,  # noqa: E712
                ModuleRolePermission.is_active == True,  # noqa: E712
            )
        )
        row = (await self.session.execute(stmt)).first()
        if not row:
            return False
        c, r, u, d = bool(row[0]), bool(row[1]), bool(row[2]), bool(row[3])
        a = (action or "").lower()
        if a == "read":
            return r
        if a == "create":
            return c
        if a == "update":
            return u
        if a == "delete":
            return d
        return False

    async def get_sidebar_menu_items(self, user_id: UUID) -> List[Dict[str, Any]]:
        """
        Menu entries from modules where ``is_menu_item`` and role has ``can_read``.

        Each item includes ``grants`` (``can_create``, ``can_read``, ``can_update``,
        ``can_delete``) for that module and the user's role.

        Storefront roles (**PUBLIC**, **CUSTOMER**) get an empty list so matrix rows
        used for catalog/checkout APIs do not surface admin sidebar tabs.
        """
        role = await self.get_user_role(user_id)
        if role and str(role.name or "").upper() in ("PUBLIC", "CUSTOMER"):
            return []

        stmt = (
            select(
                AppModule.name,
                AppModule.display_name,
                AppModule.display_order,
                AppModule.icon_key,
                ModuleRolePermission.can_create,
                ModuleRolePermission.can_read,
                ModuleRolePermission.can_update,
                ModuleRolePermission.can_delete,
            )
            .select_from(AppModule)
            .join(ModuleRolePermission, ModuleRolePermission.module_id == AppModule.id)
            .join(User, User.role_id == ModuleRolePermission.role_id)
            .where(
                User.id == user_id,
                User.is_deleted == False,  # noqa: E712
                AppModule.is_menu_item == True,  # noqa: E712
                AppModule.is_deleted == False,  # noqa: E712
                AppModule.is_active == True,  # noqa: E712
                ModuleRolePermission.can_read == True,  # noqa: E712
                ModuleRolePermission.is_deleted == False,  # noqa: E712
                ModuleRolePermission.is_active == True,  # noqa: E712
            )
            .order_by(AppModule.display_order.asc(), AppModule.display_name.asc())
        )
        result = await self.session.execute(stmt)
        items: List[Dict[str, Any]] = []
        seen: Set[str] = set()
        for (
            name,
            display_name,
            display_order_val,
            icon_key,
            can_create,
            can_read,
            can_update,
            can_delete,
        ) in result.all():
            code = str(name or "").strip()
            if not code or code in seen:
                continue
            seen.add(code)
            items.append(
                {
                    "code": code,
                    "display_name": display_name,
                    "display_order": int(display_order_val or 0),
                    "icon_key": icon_key,
                    "grants": {
                        "can_create": bool(can_create),
                        "can_read": bool(can_read),
                        "can_update": bool(can_update),
                        "can_delete": bool(can_delete),
                    },
                }
            )
        if not items and role:
            rname = str(role.name or "").upper()
            if rname not in ("PUBLIC", "CUSTOMER"):
                logger.warning(
                    "Empty menu_items for user_id=%s role=%s (no M_module_role_permissions with "
                    "can_read). From new_balan_be run: python Scripts/seed_demo_data.py --repair-rbac",
                    user_id,
                    rname,
                )
        return items


def require_module_action(module_name: str, action: Action) -> Callable:
    """
    FastAPI dependency: current user must have ``action`` on ``M_modules.name`` in
    ``M_module_role_permissions`` (see :meth:`RBACService.has_module_action`).
    """

    async def permission_dependency(
        current_user_id: UUID = Depends(get_current_user_id),
        db: AsyncSession = Depends(get_db),
    ) -> UUID:
        rbac_service = RBACService(db)
        if not await rbac_service.has_module_action(current_user_id, module_name, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {module_name}:{action} required",
            )
        return current_user_id

    return permission_dependency


def require_any_module_action(options: List[Tuple[str, Action]]) -> Callable:
    """Require at least one (module_name, action) pair on the matrix."""

    async def permission_dependency(
        current_user_id: UUID = Depends(get_current_user_id),
        db: AsyncSession = Depends(get_db),
    ) -> UUID:
        rbac_service = RBACService(db)
        for mod, act in options:
            if await rbac_service.has_module_action(current_user_id, mod, act):
                return current_user_id
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: required module access missing",
        )

    return permission_dependency
