"""
Notification master — lookup event templates for outbound pushes.
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base_repository import BaseRepository
from app.db.models import NotificationMaster


class NotificationMasterRepository(BaseRepository[NotificationMaster]):
    """Data access for ``M_notification_master``."""

    def __init__(self, session: AsyncSession):
        super().__init__(NotificationMaster, session)

    async def get_active_by_event_code(self, event_code: str) -> Optional[NotificationMaster]:
        """Return the non-deleted master row for ``event_code``, if any."""
        stmt = (
            select(self.model)
            .where(
                self.model.event_code == event_code,
                self.model.is_deleted == False,  # noqa: E712
            )
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
