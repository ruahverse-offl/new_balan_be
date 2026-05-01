"""
Notification Settings Service
Business logic for notification device settings management (admin view)
"""

from typing import Any, Dict, List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.notification_settings_repository import NotificationSettingsRepository
from app.schemas.notification_settings_schema import (
    NotificationSettingResponse,
    NotificationSettingListResponse,
)
from app.schemas.common import PaginationResponse
from app.services.base_service import BaseService


class NotificationSettingsService(BaseService):
    """Service for notification settings operations (admin)."""

    def __init__(self, session: AsyncSession):
        repository = NotificationSettingsRepository(session)
        super().__init__(repository, session)

    async def get_by_id(self, id: UUID) -> Optional[NotificationSettingResponse]:
        """Get notification setting by ID."""
        row = await self.repository.get_by_id(id)
        if not row:
            return None

        return NotificationSettingResponse(
            id=row.id,
            user_id=row.user_id,
            expo_push_token=row.expo_push_token,
            device_id=row.device_id,
            device_platform=row.device_platform,
            is_push_enabled=row.is_push_enabled,
            is_active=row.is_active,
            created_at=row.created_at,
            updated_at=row.updated_at,
            created_by=row.created_by,
            updated_by=row.updated_by,
            created_ip=row.created_ip,
            updated_ip=row.updated_ip,
            is_deleted=row.is_deleted,
        )

    async def list(
        self,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        filters: Optional[Dict[str, Any]] = None,
    ) -> NotificationSettingListResponse:
        """List notification settings with pagination."""
        rows, pagination_meta = await self.repository.get_list(
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
            additional_filters=filters or {},
        )

        items = [
            NotificationSettingResponse(
                id=row.id,
                user_id=row.user_id,
                expo_push_token=row.expo_push_token,
                device_id=row.device_id,
                device_platform=row.device_platform,
                is_push_enabled=row.is_push_enabled,
                is_active=row.is_active,
                created_at=row.created_at,
                updated_at=row.updated_at,
                created_by=row.created_by,
                updated_by=row.updated_by,
                created_ip=row.created_ip,
                updated_ip=row.updated_ip,
                is_deleted=row.is_deleted,
            )
            for row in rows
        ]

        total = pagination_meta.get("total", 0)
        has_next = (offset + limit) < total
        has_previous = offset > 0

        return NotificationSettingListResponse(
            items=items,
            pagination=PaginationResponse(
                total=total,
                limit=limit,
                offset=offset,
                has_next=has_next,
                has_previous=has_previous,
            ),
        )

    async def delete(
        self,
        id: UUID,
        deleted_by: UUID,
        deleted_ip: str,
    ) -> bool:
        """Soft delete notification setting."""
        success = await self.repository.soft_delete(id, deleted_by, deleted_ip)
        if success:
            await self.session.flush()
        return success
