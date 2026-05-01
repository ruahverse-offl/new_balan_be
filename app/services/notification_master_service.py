"""
Notification Master Service
Business logic for notification template management
"""

import json
from typing import Any, Dict, List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.notification_master_repository import NotificationMasterRepository
from app.schemas.notification_master_schema import (
    NotificationMasterCreateRequest,
    NotificationMasterUpdateRequest,
    NotificationMasterResponse,
    NotificationMasterListResponse,
)
from app.schemas.common import PaginationResponse
from app.services.base_service import BaseService


class NotificationMasterService(BaseService):
    """Service for notification master operations."""

    def __init__(self, session: AsyncSession):
        repository = NotificationMasterRepository(session)
        super().__init__(repository, session)

    def _serialize_channel_templates(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert channel_templates dict to JSON string for storage."""
        if "channel_templates" in data and isinstance(data["channel_templates"], dict):
            data["channel_templates"] = json.dumps(data["channel_templates"])
        return data

    def _deserialize_channel_templates(self, row: Any) -> Dict[str, Any]:
        """Convert channel_templates JSON string back to dict."""
        result = {
            "id": row.id,
            "event_code": row.event_code,
            "event_name": row.event_name,
            "description": row.description,
            "is_active": row.is_active,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
            "created_by": row.created_by,
            "updated_by": row.updated_by,
            "created_ip": row.created_ip,
            "updated_ip": row.updated_ip,
            "is_deleted": row.is_deleted,
        }

        # Parse channel_templates JSON
        try:
            result["channel_templates"] = json.loads(row.channel_templates) if row.channel_templates else {}
        except (json.JSONDecodeError, TypeError):
            result["channel_templates"] = {}

        return result

    async def create(
        self,
        request: NotificationMasterCreateRequest,
        created_by: UUID,
        created_ip: str,
    ) -> NotificationMasterResponse:
        """Create a new notification master template."""
        data = request.model_dump(exclude_unset=True)
        data = self._serialize_channel_templates(data)

        row = await self.repository.create(data, created_by, created_ip)
        await self.session.flush()

        return NotificationMasterResponse(**self._deserialize_channel_templates(row))

    async def get_by_id(self, id: UUID) -> Optional[NotificationMasterResponse]:
        """Get notification master by ID."""
        row = await self.repository.get_by_id(id)
        if not row:
            return None
        return NotificationMasterResponse(**self._deserialize_channel_templates(row))

    async def list(
        self,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        filters: Optional[Dict[str, Any]] = None,
    ) -> NotificationMasterListResponse:
        """List notification masters with pagination."""
        rows, pagination_meta = await self.repository.get_list(
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
            additional_filters=filters or {},
        )

        items = [
            NotificationMasterResponse(**self._deserialize_channel_templates(row))
            for row in rows
        ]

        total = pagination_meta.get("total", 0)
        has_next = (offset + limit) < total
        has_previous = offset > 0

        return NotificationMasterListResponse(
            items=items,
            pagination=PaginationResponse(
                total=total,
                limit=limit,
                offset=offset,
                has_next=has_next,
                has_previous=has_previous,
            ),
        )

    async def update(
        self,
        id: UUID,
        request: NotificationMasterUpdateRequest,
        updated_by: UUID,
        updated_ip: str,
    ) -> Optional[NotificationMasterResponse]:
        """Update notification master."""
        data = request.model_dump(exclude_unset=True)
        data = self._serialize_channel_templates(data)

        row = await self.repository.update(id, data, updated_by, updated_ip)
        if not row:
            return None

        await self.session.flush()
        return NotificationMasterResponse(**self._deserialize_channel_templates(row))

    async def delete(
        self,
        id: UUID,
        deleted_by: UUID,
        deleted_ip: str,
    ) -> bool:
        """Soft delete notification master."""
        success = await self.repository.soft_delete(id, deleted_by, deleted_ip)
        if success:
            await self.session.flush()
        return success
