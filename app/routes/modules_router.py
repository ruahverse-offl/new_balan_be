"""
Application modules (M_modules) — CRUD for access-modules RBAC.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.db.models import AppModule
from app.utils.rbac import require_module_action
from app.utils.request_utils import get_client_ip

router = APIRouter(prefix="/api/v1/modules", tags=["modules"])


class ModuleResponse(BaseModel):
    id: UUID
    name: str
    display_name: str
    is_menu_item: bool
    parent_module_id: Optional[UUID] = None
    display_order: int = 0
    icon_key: Optional[str] = None
    is_active: bool = True

    model_config = {"from_attributes": True}


class ModuleCreateRequest(BaseModel):
    name: str = Field(..., max_length=100)
    display_name: str = Field(..., max_length=255)
    is_menu_item: bool = True
    parent_module_id: Optional[UUID] = None
    display_order: int = 0
    icon_key: Optional[str] = Field(None, max_length=100)


class ModuleUpdateRequest(BaseModel):
    display_name: Optional[str] = Field(None, max_length=255)
    is_menu_item: Optional[bool] = None
    parent_module_id: Optional[UUID] = None
    display_order: Optional[int] = None
    icon_key: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


def _to_response(m: AppModule) -> ModuleResponse:
    return ModuleResponse(
        id=m.id,
        name=m.name,
        display_name=m.display_name,
        is_menu_item=bool(m.is_menu_item),
        parent_module_id=m.parent_module_id,
        display_order=int(m.display_order or 0),
        icon_key=m.icon_key,
        is_active=bool(m.is_active),
    )


@router.get("/", response_model=List[ModuleResponse])
async def list_modules(
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_module_action("access-modules", "read")),
):
    stmt = (
        select(AppModule)
        .where(AppModule.is_deleted == False)  # noqa: E712
        .order_by(AppModule.display_order.asc(), AppModule.name.asc())
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [_to_response(m) for m in rows]


@router.post("/", response_model=ModuleResponse, status_code=status.HTTP_201_CREATED)
async def create_module(
    data: ModuleCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_module_action("access-modules", "create")),
):
    ip = get_client_ip(request)
    exists = await db.execute(select(AppModule.id).where(AppModule.name == data.name.strip(), AppModule.is_deleted == False))  # noqa: E712
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Module name already exists.")
    m = AppModule(
        name=data.name.strip(),
        display_name=data.display_name.strip(),
        is_menu_item=data.is_menu_item,
        parent_module_id=data.parent_module_id,
        display_order=data.display_order or 0,
        icon_key=(data.icon_key or "").strip() or None,
        created_by=current_user_id,
        created_ip=ip,
    )
    db.add(m)
    await db.flush()
    await db.refresh(m)
    return _to_response(m)


@router.patch("/{module_id}", response_model=ModuleResponse)
async def update_module(
    module_id: UUID,
    data: ModuleUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_module_action("access-modules", "update")),
):
    ip = get_client_ip(request)
    m = await db.get(AppModule, module_id)
    if not m or m.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found.")
    patch = data.model_dump(exclude_unset=True)
    for k, v in patch.items():
        setattr(m, k, v)
    m.updated_by = current_user_id
    m.updated_ip = ip
    await db.flush()
    await db.refresh(m)
    return _to_response(m)
