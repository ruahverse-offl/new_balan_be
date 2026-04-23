"""
Role × module CRUD matrix (M_module_role_permissions).
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.db.models import AppModule, ModuleRolePermission, Role
from app.utils.rbac import require_module_action
from app.utils.request_utils import get_client_ip

router = APIRouter(prefix="/api/v1/rbac", tags=["rbac-matrix"])


class MatrixRow(BaseModel):
    module_id: UUID
    can_create: bool = False
    can_read: bool = False
    can_update: bool = False
    can_delete: bool = False


class MatrixResponse(BaseModel):
    role_id: UUID
    rows: List[MatrixRow]


class MatrixUpdateRequest(BaseModel):
    role_id: UUID
    rows: List[MatrixRow] = Field(default_factory=list)


async def _load_matrix(db: AsyncSession, role_id: UUID) -> MatrixResponse:
    r = await db.get(Role, role_id)
    if not r or r.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")
    mods = (await db.execute(select(AppModule).where(AppModule.is_deleted == False))).scalars().all()  # noqa: E712
    grants = (
        await db.execute(
            select(ModuleRolePermission).where(
                ModuleRolePermission.role_id == role_id,
                ModuleRolePermission.is_deleted == False,  # noqa: E712
            )
        )
    ).scalars().all()
    by_mod = {g.module_id: g for g in grants}
    rows: List[MatrixRow] = []
    for m in mods:
        g = by_mod.get(m.id)
        if g:
            rows.append(
                MatrixRow(
                    module_id=m.id,
                    can_create=bool(g.can_create),
                    can_read=bool(g.can_read),
                    can_update=bool(g.can_update),
                    can_delete=bool(g.can_delete),
                )
            )
        else:
            rows.append(MatrixRow(module_id=m.id))
    return MatrixResponse(role_id=role_id, rows=rows)


@router.get("/matrix", response_model=MatrixResponse)
async def get_role_matrix(
    role_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_module_action("role-access", "read")),
):
    return await _load_matrix(db, role_id)


@router.put("/matrix", response_model=MatrixResponse)
async def put_role_matrix(
    data: MatrixUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_module_action("role-access", "update")),
):
    ip = get_client_ip(request)
    r = await db.get(Role, data.role_id)
    if not r or r.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")
    # Soft-delete existing grants for this role
    existing = (
        await db.execute(
            select(ModuleRolePermission).where(
                ModuleRolePermission.role_id == data.role_id,
                ModuleRolePermission.is_deleted == False,  # noqa: E712
            )
        )
    ).scalars().all()
    for row in existing:
        row.is_deleted = True
        row.updated_by = current_user_id
        row.updated_ip = ip
    by_module: dict[UUID, MatrixRow] = {}
    for row in data.rows:
        by_module[row.module_id] = row
    for mid, row in by_module.items():
        m = await db.get(AppModule, mid)
        if not m or m.is_deleted:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid module_id {mid}")
        any_flag = row.can_create or row.can_read or row.can_update or row.can_delete
        if not any_flag:
            continue
        db.add(
            ModuleRolePermission(
                module_id=row.module_id,
                role_id=data.role_id,
                can_create=row.can_create,
                can_read=row.can_read,
                can_update=row.can_update,
                can_delete=row.can_delete,
                created_by=current_user_id,
                created_ip=ip,
            )
        )
    await db.flush()
    return await _load_matrix(db, data.role_id)
