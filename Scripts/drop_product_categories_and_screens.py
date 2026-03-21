"""
Drop legacy tables removed from the application:
  - product_categories (product category master — feature removed)
  - screens (optional — only if a custom table with this name exists)

Run from the backend root with the same .env as the API:
  python Scripts/drop_product_categories_and_screens.py

Requires DATABASE_URL (or DB_* vars) to point at your PostgreSQL instance.
"""
import asyncio
import sys
from pathlib import Path

# Allow importing app.* when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from app.db.db_connection import DatabaseConnection


async def main() -> None:
    DatabaseConnection.initialize()
    factory = DatabaseConnection.get_session_factory()

    async with factory() as session:
        await session.execute(text("DROP TABLE IF EXISTS product_categories CASCADE"))
        await session.execute(text("DROP TABLE IF EXISTS screens CASCADE"))
        await session.commit()
        print("OK: Dropped product_categories (if existed) and screens (if existed).")


if __name__ == "__main__":
    asyncio.run(main())
