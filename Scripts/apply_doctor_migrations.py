"""
Apply doctor table migrations using only DATABASE_URL (same as the API).

Usage (from repo root: folder that contains app/ and migrations/):

    set DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
    python Scripts/apply_doctor_migrations.py

Or put DATABASE_URL in a .env file next to app/ (backend project root).

Supports URLs starting with postgresql://, postgres://, or postgresql+asyncpg://
(managed hosts often give postgres:// or postgresql://).
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(_ROOT / ".env")
except ImportError:
    pass

import asyncpg

# Order matters for logical grouping; each file uses IF NOT EXISTS where applicable.
MIGRATIONS = [
    "order_fulfillment_lifecycle.sql",
    "doctor_extended_profile.sql",
    "doctor_timing_time_columns.sql",
]


def dsn_for_asyncpg(database_url: str) -> str:
    u = database_url.strip().strip('"').strip("'")
    if u.startswith("postgresql+asyncpg://"):
        return "postgresql://" + u[len("postgresql+asyncpg://") :]
    if u.startswith("postgres://"):
        return "postgresql://" + u[len("postgres://") :]
    return u


def statements_from_sql(content: str) -> list[str]:
    """Split on ';' and drop comment-only chunks (sufficient for our migration files)."""
    out: list[str] = []
    for chunk in content.split(";"):
        lines = [
            line
            for line in chunk.splitlines()
            if line.strip() and not line.strip().startswith("--")
        ]
        if lines:
            out.append("\n".join(lines).strip())
    return out


async def main() -> None:
    url = os.environ.get("DATABASE_URL")
    if not url:
        print(
            "Missing DATABASE_URL. Set it in the environment or in .env at:\n"
            f"  {_ROOT / '.env'}",
            file=sys.stderr,
        )
        sys.exit(1)

    dsn = dsn_for_asyncpg(url)
    mig_dir = _ROOT / "migrations"

    conn = await asyncpg.connect(dsn)
    try:
        for name in MIGRATIONS:
            path = mig_dir / name
            if not path.is_file():
                print(f"Skip (file not found): {path}", file=sys.stderr)
                continue
            sql_text = path.read_text(encoding="utf-8")
            for stmt in statements_from_sql(sql_text):
                await conn.execute(stmt)
            print(f"Applied: {name}")
        print("Done.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
