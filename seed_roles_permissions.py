"""
Seed script to ensure staff roles have permissions needed to see Orders, Payments, and Dashboards.
Run from backend directory: python seed_roles_permissions.py

- Ensures required permission codes exist in `permissions`.
- Assigns ORDER_VIEW, DASHBOARD_VIEW, ORDER_UPDATE, PAYMENT_PROCESS to staff roles
  (admin, manager, cashier, customer_service) so they can see data in the admin panel.
"""
import asyncio
from uuid import uuid4
from sqlalchemy import text
from app.db.db_connection import DatabaseConnection


# Permissions that staff need to see orders, payments, dashboards, and inventory
STAFF_VIEW_PERMISSIONS = [
    "ORDER_VIEW",
    "DASHBOARD_VIEW",
    "ORDER_UPDATE",
    "PAYMENT_PROCESS",
    "INVENTORY_VIEW",
]

# Role names (case-insensitive) that should get these permissions
STAFF_ROLE_NAMES = {"admin", "manager", "cashier", "customer_service", "customer service"}


async def seed():
    DatabaseConnection.initialize()
    factory = DatabaseConnection.get_session_factory()

    async with factory() as session:
        # Get a system user for created_by (first user in DB, or we use a placeholder and rely on existing rows)
        r = await session.execute(text("SELECT id FROM users WHERE is_deleted = false LIMIT 1"))
        row = r.fetchone()
        created_by = str(row.id) if row else "00000000-0000-0000-0000-000000000000"
        created_ip = "127.0.0.1"

        # 1. Ensure permissions exist
        for code in STAFF_VIEW_PERMISSIONS:
            r = await session.execute(
                text("SELECT id FROM permissions WHERE code = :code AND is_deleted = false"),
                {"code": code},
            )
            if r.fetchone() is None:
                perm_id = str(uuid4())
                await session.execute(
                    text("""
                        INSERT INTO permissions (id, code, description, is_active, is_deleted, created_by, created_ip)
                        VALUES (:id, :code, :desc, true, false, :created_by, :created_ip)
                    """),
                    {
                        "id": perm_id,
                        "code": code,
                        "desc": f"Permission: {code}",
                        "created_by": created_by,
                        "created_ip": created_ip,
                    },
                )
                print(f"  Created permission: {code}")
            else:
                print(f"  Permission exists: {code}")

        # 2. Get permission IDs by code
        r = await session.execute(
            text("SELECT id, code FROM permissions WHERE is_deleted = false AND code = ANY(:codes)"),
            {"codes": list(STAFF_VIEW_PERMISSIONS)},
        )
        perm_map = {row.code: str(row.id) for row in r.fetchall()}

        # 3. Get staff roles (name matches, case-insensitive; exclude CUSTOMER)
        r = await session.execute(
            text("SELECT id, name FROM roles WHERE is_deleted = false")
        )
        staff_roles = []
        for row in r.fetchall():
            name_upper = (row.name or "").strip().upper().replace(" ", "_")
            name_lower = (row.name or "").strip().lower()
            if name_upper == "CUSTOMER":
                continue
            if name_upper in ("ADMIN", "MANAGER", "CASHIER", "CUSTOMER_SERVICE") or name_lower in STAFF_ROLE_NAMES:
                staff_roles.append((str(row.id), row.name))
            # Also treat any role that is not CUSTOMER as staff for minimal view access
            elif name_upper and name_upper != "CUSTOMER":
                staff_roles.append((str(row.id), row.name))

        # Dedupe by role id
        seen = set()
        unique_staff_roles = []
        for rid, rname in staff_roles:
            if rid not in seen:
                seen.add(rid)
                unique_staff_roles.append((rid, rname))

        # 4. For each staff role, ensure it has each permission (insert role_permissions if missing)
        for role_id, role_name in unique_staff_roles:
            for perm_code, perm_id in perm_map.items():
                r = await session.execute(
                    text("""
                        SELECT 1 FROM role_permissions
                        WHERE role_id = :role_id AND permission_id = :perm_id AND is_deleted = false
                    """),
                    {"role_id": role_id, "perm_id": perm_id},
                )
                if r.fetchone() is None:
                    rp_id = str(uuid4())
                    await session.execute(
                        text("""
                            INSERT INTO role_permissions (id, role_id, permission_id, is_active, is_deleted, created_by, created_ip)
                            VALUES (:id, :role_id, :permission_id, true, false, :created_by, :created_ip)
                        """),
                        {
                            "id": rp_id,
                            "role_id": role_id,
                            "permission_id": perm_id,
                            "created_by": created_by,
                            "created_ip": created_ip,
                        },
                    )
                    print(f"  Assigned {perm_code} -> role '{role_name}' ({role_id[:8]}...)")

        await session.commit()
        print("\nRoles/permissions seed completed. Staff should now see Orders, Payments, and Dashboards.")


if __name__ == "__main__":
    asyncio.run(seed())
