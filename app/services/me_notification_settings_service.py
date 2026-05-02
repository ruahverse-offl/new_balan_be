"""
Register / upsert FCM device token rows for the current user (``M_notification_settings``).
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import NotificationSetting
from app.repositories.notification_settings_repository import NotificationSettingsRepository
from app.schemas.notification_settings_schema import (
    MeNotificationSettingRegisterRequest,
    MeNotificationSettingRevokeRequest,
)


class MeNotificationSettingsService:
    """Upsert notification settings for JWT-authenticated mobile clients."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def upsert_my_device(
        self,
        user_id: UUID,
        body: MeNotificationSettingRegisterRequest,
        client_ip: str,
    ) -> NotificationSetting:
        """
        Create or update the row for (``user_id``, ``expo_push_token``).

        Revives soft-deleted rows when the same token is registered again.
        """
        repo = NotificationSettingsRepository(self._session)
        existing = await repo.get_by_user_id_and_expo_token(user_id, body.expo_push_token)

        if existing:
            existing.device_id = body.device_id
            existing.device_platform = body.device_platform
            existing.is_push_enabled = body.is_push_enabled
            existing.is_active = True
            existing.is_deleted = False
            existing.updated_by = user_id
            existing.updated_ip = client_ip
            await self._session.flush()
            await self._session.refresh(existing)
            return existing

        return await repo.create(
            {
                "user_id": user_id,
                "expo_push_token": body.expo_push_token,
                "device_id": body.device_id,
                "device_platform": body.device_platform,
                "is_push_enabled": body.is_push_enabled,
                "is_active": True,
            },
            user_id,
            client_ip,
        )

    async def revoke_my_devices(
        self,
        user_id: UUID,
        body: MeNotificationSettingRevokeRequest,
        client_ip: str,
    ) -> int:
        """
        Soft-delete matching ``M_notification_settings`` rows for this user (logout / sign-out).

        Deduplicates by row id when both ``expo_push_token`` and ``device_id`` match the same row.
        """
        repo = NotificationSettingsRepository(self._session)
        ids: set[UUID] = set()

        if body.expo_push_token:
            row = await repo.get_by_user_id_and_expo_token(user_id, body.expo_push_token)
            if row and not row.is_deleted:
                ids.add(row.id)

        if body.device_id:
            for row in await repo.list_active_by_user_and_device_id(user_id, body.device_id):
                ids.add(row.id)

        for row_id in ids:
            await repo.soft_delete(row_id, user_id, client_ip)

        return len(ids)
