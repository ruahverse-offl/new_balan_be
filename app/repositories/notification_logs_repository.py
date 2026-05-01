"""
Notification logs repository — list rows for a user (in-app notification center).
"""

from typing import List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base_repository import BaseRepository
from app.db.models import NotificationLog


class NotificationLogsRepository(BaseRepository[NotificationLog]):
    """Data access for ``T_notification_logs``."""

    def __init__(self, session: AsyncSession):
        super().__init__(NotificationLog, session)

    async def list_for_user(self, user_id: UUID, *, limit: int, offset: int = 0) -> List[NotificationLog]:
        """Latest notification attempts for the user, newest first."""
        stmt = (
            select(self.model)
            .where(
                self.model.is_deleted == False,  # noqa: E712
                self.model.user_id == user_id,
            )
            .order_by(self.model.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
