"""
Notification Logs Admin Service
Business logic for notification logs management (admin view)
"""

import json
from typing import Any, Dict, List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.notification_logs_repository import NotificationLogsRepository
from app.schemas.notification_logs_schema import (
    NotificationLogResponse,
    NotificationLogListResponse,
)
from app.schemas.common import PaginationResponse
from app.services.base_service import BaseService
from app.db.models import User, NotificationMaster


class NotificationLogsAdminService(BaseService):
    """Service for notification logs operations (admin)."""

    def __init__(self, session: AsyncSession):
        repository = NotificationLogsRepository(session)
        super().__init__(repository, session)

    def _parse_json_field(self, field: Any) -> Dict[str, Any]:
        """Parse JSON field safely."""
        if field is None:
            return {}
        if isinstance(field, dict):
            return field
        if isinstance(field, str):
            try:
                return json.loads(field) if field.strip() else {}
            except json.JSONDecodeError:
                return {}
        return {}

    async def _fetch_user_map(self, user_ids) -> Dict[UUID, str]:
        if not user_ids:
            return {}
        result = await self.session.execute(
            select(User.id, User.full_name).where(User.id.in_(user_ids))
        )
        return {uid: name for uid, name in result}

    async def _fetch_event_map(self, master_ids) -> Dict[UUID, str]:
        if not master_ids:
            return {}
        result = await self.session.execute(
            select(NotificationMaster.id, NotificationMaster.event_code).where(
                NotificationMaster.id.in_(master_ids)
            )
        )
        return {mid: code for mid, code in result}

    async def get_by_id(self, id: UUID) -> Optional[NotificationLogResponse]:
        """Get notification log by ID."""
        row = await self.repository.get_by_id(id)
        if not row:
            return None

        user_map = await self._fetch_user_map([row.user_id])
        event_map = await self._fetch_event_map([row.notification_master_id])

        return NotificationLogResponse(
            id=row.id,
            user_id=row.user_id,
            user_name=user_map.get(row.user_id),
            notification_master_id=row.notification_master_id,
            event_code=event_map.get(row.notification_master_id),
            notification_setting_id=row.notification_setting_id,
            channel=row.channel,
            expo_push_token=row.expo_push_token,
            payload_snapshot=self._parse_json_field(row.payload_snapshot),
            send_status=row.send_status,
            provider_response=row.provider_response,
            error_message=row.error_message,
            retry_count=row.retry_count,
            max_retry_attempts=row.max_retry_attempts,
            sent_at=row.sent_at,
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
    ) -> NotificationLogListResponse:
        """List notification logs with pagination."""
        rows, pagination_meta = await self.repository.get_list(
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
            additional_filters=filters or {},
        )

        user_ids = list({row.user_id for row in rows})
        master_ids = list({row.notification_master_id for row in rows})
        user_map = await self._fetch_user_map(user_ids)
        event_map = await self._fetch_event_map(master_ids)

        items = [
            NotificationLogResponse(
                id=row.id,
                user_id=row.user_id,
                user_name=user_map.get(row.user_id),
                notification_master_id=row.notification_master_id,
                event_code=event_map.get(row.notification_master_id),
                notification_setting_id=row.notification_setting_id,
                channel=row.channel,
                expo_push_token=row.expo_push_token,
                payload_snapshot=self._parse_json_field(row.payload_snapshot),
                send_status=row.send_status,
                provider_response=row.provider_response,
                error_message=row.error_message,
                retry_count=row.retry_count,
                max_retry_attempts=row.max_retry_attempts,
                sent_at=row.sent_at,
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

        return NotificationLogListResponse(
            items=items,
            pagination=PaginationResponse(
                total=total,
                limit=limit,
                offset=offset,
                has_next=has_next,
                has_previous=has_previous,
            ),
        )
