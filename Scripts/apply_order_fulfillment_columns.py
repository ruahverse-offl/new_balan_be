"""
Apply T_orders fulfillment columns (same SQL as API startup patch).

Use if you prefer a one-off script without starting the server:

    python Scripts/apply_order_fulfillment_columns.py

The API runs this automatically after create_all() on PostgreSQL (see app.db.db_connection).
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(_ROOT / ".env")
except ImportError:
    pass

from sqlalchemy.ext.asyncio import create_async_engine

from app.db.order_fulfillment_schema import apply_order_fulfillment_schema


async def main() -> None:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        print("DATABASE_URL is not set.", file=sys.stderr)
        sys.exit(1)
    if "postgresql" not in url:
        print("This migration applies to PostgreSQL only.", file=sys.stderr)
        sys.exit(1)

    engine = create_async_engine(url)
    try:
        async with engine.begin() as conn:
            if conn.dialect.name != "postgresql":
                print("Expected PostgreSQL dialect.", file=sys.stderr)
                sys.exit(1)
            await apply_order_fulfillment_schema(conn)
        print("T_orders fulfillment schema applied.")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
