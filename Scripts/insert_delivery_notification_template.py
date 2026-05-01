"""
Insert DELIVERY_ASSIGNED notification template into M_notification_master table.

Run this script to manually create the notification template before testing.
"""

import asyncio
import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

import sys
from pathlib import Path

# Add parent directory to path so we can import from app
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings
from app.db.models import NotificationMaster, User


async def main():
    """Insert DELIVERY_ASSIGNED notification template."""
    settings = get_settings()

    # Create async engine
    if not settings.DATABASE_URL:
        print("❌ DATABASE_URL not found in settings. Please check your .env file.")
        return

    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
    )

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Check if template already exists
            result = await session.execute(
                select(NotificationMaster).where(
                    NotificationMaster.event_code == "DELIVERY_ASSIGNED",
                    NotificationMaster.is_deleted == False,  # noqa: E712
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                print("[SUCCESS] DELIVERY_ASSIGNED notification template already exists:")
                print(f"   ID: {existing.id}")
                print(f"   Event: {existing.event_name}")
                print(f"   Description: {existing.description}")
                print(f"   Active: {existing.is_active}")
                print(f"   Template: {existing.channel_templates}")
                return

            # Get first admin user for audit fields
            admin_result = await session.execute(
                select(User).where(User.is_deleted == False).limit(1)  # noqa: E712
            )
            admin_user = admin_result.scalar_one_or_none()
            audit_user_id = admin_user.id if admin_user else uuid4()

            # Prepare notification template
            channel_templates = {
                "push": {
                    "title_template": "New delivery assigned",
                    "body_template": "Order {{order_reference}} for {{customer_name}}. Open the app to view.",
                    "message_variables": ["order_reference", "customer_name", "order_status", "delivery_address"],
                    "is_enabled": True,
                }
            }

            # Create notification master
            notification_master = NotificationMaster(
                id=uuid4(),
                event_code="DELIVERY_ASSIGNED",
                event_name="Delivery assigned",
                description="Fired when staff assigns or reassigns a delivery agent to an order",
                channel_templates=json.dumps(channel_templates),
                is_active=True,
                is_deleted=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                created_by=audit_user_id,
                updated_by=audit_user_id,
                created_ip="127.0.0.1",
                updated_ip="127.0.0.1",
            )

            session.add(notification_master)
            await session.commit()

            print("✅ DELIVERY_ASSIGNED notification template created successfully!")
            print(f"   ID: {notification_master.id}")
            print(f"   Event Code: {notification_master.event_code}")
            print(f"   Event Name: {notification_master.event_name}")
            print(f"   Description: {notification_master.description}")
            print(f"   Active: {notification_master.is_active}")
            print(f"   Template: {notification_master.channel_templates}")

        except Exception as e:
            print(f"❌ Error creating notification template: {e}")
            await session.rollback()
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
