"""
Ensure notification tables exist in PostgreSQL.

Run:
    python Scripts/apply_notification_tables.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from sqlalchemy import text

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.db.db_connection import DatabaseConnection
from app.db.models import NotificationLog, NotificationMaster, NotificationSetting


async def main() -> None:
    os.chdir(_ROOT)
    DatabaseConnection.initialize()
    engine = DatabaseConnection.get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(NotificationMaster.__table__.create, checkfirst=True)
        await conn.run_sync(NotificationSetting.__table__.create, checkfirst=True)
        await conn.run_sync(NotificationLog.__table__.create, checkfirst=True)
        rows = await conn.execute(
            text(
                """
                select tablename
                from pg_tables
                where schemaname = 'public'
                  and tablename in ('M_notification_master', 'M_notification_settings', 'T_notification_logs')
                order by tablename
                """
            )
        )
        print("notification_tables:", [r[0] for r in rows.fetchall()])
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

