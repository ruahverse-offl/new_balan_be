"""
Seed RBAC (roles, permissions, role_permissions, users) for a fresh database.
Run from backend directory: PYTHONIOENCODING=utf-8 python Scripts/seed_rbac_data.py

WARNING: Deletes all existing users, role_permissions, permissions, and roles
before re-creating them. Run this FIRST before seed_roles_permissions.py or seed_demo_data.py.
"""
import asyncio
import os
import sys
from uuid import uuid4

# Ensure backend root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.db_connection import DatabaseConnection
from app.utils.password import hash_password


# System UUID used as created_by when no users exist yet
SYSTEM_UUID = "00000000-0000-0000-0000-000000000001"
DEFAULT_PASSWORD = "NewBalan@2026"

ROLES = [
    ("DEV_ADMIN", "Development admin – full access including RBAC"),
    ("ADMIN", "Administrator – full operational access"),
    ("MANAGER", "Store manager"),
    ("PHARMACIST", "Pharmacist – prescription review, orders"),
    ("CASHIER", "Cashier – order processing, payments"),
    ("CUSTOMER_SERVICE", "Customer service – appointments, test bookings"),
    ("CUSTOMER", "Customer – shopping, booking"),
]

# All permission codes referenced in the app (routers + seed_roles_permissions)
PERMISSIONS = [
    "ROLE_CREATE", "ROLE_VIEW", "ROLE_UPDATE", "ROLE_DELETE",
    "ROLE_PERMISSION_CREATE", "ROLE_PERMISSION_VIEW", "ROLE_PERMISSION_UPDATE", "ROLE_PERMISSION_DELETE",
    "PERMISSION_CREATE", "PERMISSION_VIEW", "PERMISSION_UPDATE", "PERMISSION_DELETE",
    "ORDER_CREATE", "ORDER_VIEW", "ORDER_UPDATE",
    "DASHBOARD_VIEW",
    "PAYMENT_PROCESS",
    "INVENTORY_VIEW", "INVENTORY_UPDATE",
    "MEDICINE_CREATE", "MEDICINE_VIEW", "MEDICINE_UPDATE", "MEDICINE_DELETE",
    "MEDICINE_CATEGORY_MANAGE",
    "PRESCRIPTION_APPROVE", "PRESCRIPTION_REVIEW",
    "APPOINTMENT_VIEW", "APPOINTMENT_UPDATE", "APPOINTMENT_DELETE",
    "STAFF_CREATE", "STAFF_UPDATE", "STAFF_DELETE",
    "COUPON_CREATE", "COUPON_VIEW",
]

# Role name -> list of permission codes (DEV_ADMIN gets all)
STAFF_PERMISSIONS = [
    "ORDER_CREATE", "ORDER_VIEW", "ORDER_UPDATE", "DASHBOARD_VIEW", "PAYMENT_PROCESS", "INVENTORY_VIEW", "INVENTORY_UPDATE",
    "MEDICINE_CREATE", "MEDICINE_VIEW", "MEDICINE_UPDATE", "MEDICINE_DELETE", "MEDICINE_CATEGORY_MANAGE",
    "PRESCRIPTION_APPROVE", "PRESCRIPTION_REVIEW",
    "APPOINTMENT_VIEW", "APPOINTMENT_UPDATE", "APPOINTMENT_DELETE",
    "STAFF_CREATE", "STAFF_UPDATE", "STAFF_DELETE",
    "COUPON_CREATE", "COUPON_VIEW",
]
ADMIN_EXTRA = ["ROLE_CREATE", "ROLE_VIEW", "ROLE_UPDATE", "ROLE_DELETE", "ROLE_PERMISSION_CREATE", "ROLE_PERMISSION_VIEW", "ROLE_PERMISSION_UPDATE", "ROLE_PERMISSION_DELETE", "PERMISSION_CREATE", "PERMISSION_VIEW", "PERMISSION_UPDATE", "PERMISSION_DELETE"]

USERS = [
    ("devadmin@newbalan.com", "DEV_ADMIN", "Dev Admin", "9999999999"),
    ("admin@newbalan.com", "ADMIN", "Admin User", "9999999998"),
    ("manager@newbalan.com", "MANAGER", "Manager User", "9999999997"),
    ("pharmacist@newbalan.com", "PHARMACIST", "Pharmacist User", "9999999996"),
    ("cashier@newbalan.com", "CASHIER", "Cashier User", "9999999995"),
    ("customerservice@newbalan.com", "CUSTOMER_SERVICE", "Customer Service", "9999999994"),
    ("customer@newbalan.com", "CUSTOMER", "Customer User", "9999999993"),
]


async def seed():
    DatabaseConnection.initialize()
    factory = DatabaseConnection.get_session_factory()
    created_ip = "127.0.0.1"

    async with factory() as session:
        # 1. Create tables if they don't exist (e.g. fresh DB)
        try:
            await DatabaseConnection.create_tables()
        except Exception as e:
            print(f"[WARN] create_tables: {e}")

        # 2. Hard-delete RBAC data (order matters: FKs)
        for table in ("role_permissions", "users", "permissions", "roles"):
            try:
                await session.execute(text(f"DELETE FROM {table}"))
                print(f"  Cleared {table}")
            except Exception as e:
                print(f"  Skip {table}: {e}")
        await session.commit()

        # 3. Insert roles
        role_ids = {}
        for name, desc in ROLES:
            rid = str(uuid4())
            role_ids[name] = rid
            await session.execute(
                text("""
                    INSERT INTO roles (id, name, description, is_active, is_deleted, created_by, created_ip)
                    VALUES (:id, :name, :desc, true, false, :cb, :ip)
                """),
                {"id": rid, "name": name, "desc": desc or "", "cb": SYSTEM_UUID, "ip": created_ip},
            )
        print(f"  Inserted {len(ROLES)} roles")

        # 4. Insert permissions
        perm_ids = {}
        for code in PERMISSIONS:
            pid = str(uuid4())
            perm_ids[code] = pid
            await session.execute(
                text("""
                    INSERT INTO permissions (id, code, description, is_active, is_deleted, created_by, created_ip)
                    VALUES (:id, :code, :desc, true, false, :cb, :ip)
                """),
                {"id": pid, "code": code, "desc": f"Permission: {code}", "cb": SYSTEM_UUID, "ip": created_ip},
            )
        print(f"  Inserted {len(PERMISSIONS)} permissions")

        # 5. Role-permission mappings
        def perms_for_role(role_name: str):
            if role_name == "DEV_ADMIN":
                return list(PERMISSIONS)
            if role_name == "ADMIN":
                return list(set(STAFF_PERMISSIONS + ADMIN_EXTRA))
            if role_name in ("MANAGER", "PHARMACIST", "CASHIER", "CUSTOMER_SERVICE"):
                return list(STAFF_PERMISSIONS)
            return []  # CUSTOMER

        rp_count = 0
        for role_name, role_id in role_ids.items():
            for code in perms_for_role(role_name):
                if code not in perm_ids:
                    continue
                rp_id = str(uuid4())
                await session.execute(
                    text("""
                        INSERT INTO role_permissions (id, role_id, permission_id, is_active, is_deleted, created_by, created_ip)
                        VALUES (:id, :role_id, :perm_id, true, false, :cb, :ip)
                    """),
                    {"id": rp_id, "role_id": role_id, "perm_id": perm_ids[code], "cb": SYSTEM_UUID, "ip": created_ip},
                )
                rp_count += 1
        print(f"  Inserted {rp_count} role_permissions")

        # 6. Users (password: NewBalan@2026)
        pw_hash = hash_password(DEFAULT_PASSWORD)
        for email, role_name, full_name, mobile in USERS:
            uid = str(uuid4())
            role_id = role_ids[role_name]
            await session.execute(
                text("""
                    INSERT INTO users (id, role_id, full_name, mobile_number, email, password_hash, is_active, is_deleted, created_by, created_ip)
                    VALUES (:id, :role_id, :name, :mobile, :email, :pw, true, false, :cb, :ip)
                """),
                {
                    "id": uid,
                    "role_id": role_id,
                    "name": full_name,
                    "mobile": mobile,
                    "email": email,
                    "pw": pw_hash,
                    "cb": SYSTEM_UUID,
                    "ip": created_ip,
                },
            )
        print(f"  Inserted {len(USERS)} users")

        await session.commit()
    print("\n[OK] RBAC seed completed. All passwords: NewBalan@2026")
    await DatabaseConnection.close()


if __name__ == "__main__":
    asyncio.run(seed())
