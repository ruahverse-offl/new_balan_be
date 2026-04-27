"""
Demo seed: RBAC (roles, modules, matrix), staff + customer users, catalog, and sample orders.

Run from backend root with DATABASE_URL set and venv active::

    python Scripts/seed_demo_data.py
    python Scripts/seed_demo_data.py --force      # remove prior DEMO-* seed rows and re-insert
    python Scripts/seed_demo_data.py --wipe-db    # create_all if needed, TRUNCATE all app tables, then seed
    python Scripts/seed_demo_data.py --repair-rbac  # upsert M_module_role_permissions only (fixes empty admin menu)

Default password for all seeded users: NewBalan@2026

Users:
  admin@newbalan.com          -> ADMIN
  devadmin@newbalan.com       -> DEV_ADMIN
  manager@newbalan.com        -> MANAGER
  deliveryagent@newbalan.com  -> DELIVERY_AGENT
  customer@newbalan.com       -> CUSTOMER (end customer)

Catalog: 4 categories, 4 brands, 10 medicines (each with one offering + inventory).
Orders: 20 rows with order_reference DEMO-SEED-01 .. DEMO-SEED-20 at varied lifecycle statuses.
Also: delivery settings, doctors + appointments, polyclinic tests + bookings, coupons (+ one usage),
customer saved addresses, and one low-stock inventory alert.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Tuple
from uuid import UUID, uuid4

# Allow ``python Scripts/seed_demo_data.py`` from repo root
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import Base, DatabaseConnection
from app.db.models import (
    Address,
    AppModule,
    Appointment,
    Brand,
    Coupon,
    CouponUsage,
    DeliverySetting,
    Doctor,
    Inventory,
    InventoryAlert,
    Medicine,
    MedicineBrandOffering,
    MedicineCategory,
    ModuleRolePermission,
    NotificationLog,
    NotificationMaster,
    NotificationSetting,
    Order,
    OrderItem,
    Payment,
    PolyclinicTest,
    Role,
    TestBooking,
    User,
)
from app.domain import order_lifecycle as lc
from app.utils.datetime_utils import IST
from app.utils.password import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_demo")

SEED_IP = "127.0.0.1"
ACTOR = UUID("00000000-0000-0000-0000-000000000001")
DEMO_PREFIX = "DEMO"
ORDER_REF_PREFIX = "DEMO-SEED-"
PLAIN_PASSWORD = "NewBalan@2026"

MODULE_ROWS: List[Tuple[str, str, int, str]] = [
    ("roles", "Roles", 5, "Shield"),
    ("access-modules", "App modules", 6, "Layers"),
    ("role-access", "Role × module access", 7, "Grid3x3"),
    ("doctors", "Manage Doctors", 10, "Users"),
    ("medicines", "Manage Medicines", 20, "Pill"),
    ("therapeutic-categories", "Medicine Cat.", 25, "Tags"),
    ("inventory", "Inventory", 26, "Package"),
    ("brand-master", "Brand catalog", 27, "Tag"),
    # display_order 1 = default staff landing tab (see Admin.jsx getDefaultAdminLandingTabId)
    ("orders", "Orders", 1, "ShoppingCart"),
    ("delivery-orders", "My deliveries", 31, "Truck"),
    ("appointments", "Appointments", 40, "Clock"),
    ("delivery", "Delivery Settings", 50, "Truck"),
    ("coupons", "Coupons & Marquee", 60, "Ticket"),
    ("staff", "Manage Staff", 70, "UserCheck"),
    ("test-bookings", "Test Bookings", 80, "Calendar"),
    ("notification-master", "Notification Master", 81, "Bell"),
    ("notification-settings", "Notification Settings", 82, "Bell"),
    ("notification-logs", "Notification Logs", 83, "Bell"),
    ("payments", "Payments", 90, "CreditCard"),
    ("coupon-usages", "Coupon Usages", 100, "BarChart3"),
]

ROLE_ROWS: List[Tuple[str, str]] = [
    ("ADMIN", "Operational admin; no RBAC tabs."),
    ("DEV_ADMIN", "RBAC administration only."),
    ("MANAGER", "Operational manager; full CRUD on non-RBAC modules."),
    ("DELIVERY_AGENT", "Assigned deliveries only."),
    ("PUBLIC", "Storefront self-signup; orders require login."),
    ("CUSTOMER", "End customer who places orders (legacy; same matrix as PUBLIC)."),
]

USER_SPECS: List[Tuple[str, str, str, str]] = [
    ("admin@newbalan.com", "ADMIN", "Demo Admin", "9999999901"),
    ("devadmin@newbalan.com", "DEV_ADMIN", "Demo Dev Admin", "9999999902"),
    ("manager@newbalan.com", "MANAGER", "Demo Manager", "9999999903"),
    ("deliveryagent@newbalan.com", "DELIVERY_AGENT", "Demo Delivery Agent", "9999999904"),
    ("customer@newbalan.com", "CUSTOMER", "Demo Customer", "9999999905"),
]

# (role_name, module_name, c, r, u, d)
MATRIX: List[Tuple[str, str, bool, bool, bool, bool]] = []

# ADMIN & MANAGER: full CRUD except RBAC trio
for rname in ("ADMIN", "MANAGER"):
    for mname, _, _, _ in MODULE_ROWS:
        if mname in ("roles", "access-modules", "role-access"):
            continue
        MATRIX.append((rname, mname, True, True, True, True))

# DEV_ADMIN: RBAC only
for mname in ("roles", "access-modules", "role-access"):
    MATRIX.append(("DEV_ADMIN", mname, True, True, True, True))

# DELIVERY_AGENT
MATRIX.append(("DELIVERY_AGENT", "delivery-orders", False, True, True, False))

# PUBLIC + CUSTOMER storefront (see ACCESS_AND_ROLES.md)
for rname in ("PUBLIC", "CUSTOMER"):
    MATRIX.extend(
        [
            (rname, "medicines", False, True, False, False),
            (rname, "therapeutic-categories", False, True, False, False),
            (rname, "inventory", False, True, False, False),
            (rname, "brand-master", False, True, False, False),
            (rname, "orders", True, True, False, False),
            (rname, "coupon-usages", True, True, False, False),
        ]
    )


def _now() -> datetime:
    return datetime.now(IST)


async def _table_exists(session: AsyncSession, table_name: str) -> bool:
    """Return True when table exists in current PostgreSQL schema."""
    exists = await session.scalar(
        text(
            """
            select 1
            from pg_tables
            where schemaname = 'public'
              and tablename = :table_name
            limit 1
            """
        ),
        {"table_name": table_name},
    )
    return bool(exists)


async def _get_or_create_role(session: AsyncSession, name: str, description: str) -> Role:
    q = await session.execute(select(Role).where(Role.name == name, Role.is_deleted == False))  # noqa: E712
    row = q.scalar_one_or_none()
    if row:
        return row
    role = Role(
        name=name,
        description=description,
        created_by=ACTOR,
        created_ip=SEED_IP,
        is_deleted=False,
        is_active=True,
    )
    session.add(role)
    await session.flush()
    logger.info("Created role %s", name)
    return role


async def _get_or_create_module(session: AsyncSession, name: str, display_name: str, ord_: int, icon_key: str) -> AppModule:
    q = await session.execute(select(AppModule).where(AppModule.name == name, AppModule.is_deleted == False))  # noqa: E712
    row = q.scalar_one_or_none()
    if row:
        return row
    mod = AppModule(
        name=name,
        display_name=display_name,
        is_menu_item=True,
        parent_module_id=None,
        display_order=ord_,
        icon_key=icon_key,
        created_by=ACTOR,
        created_ip=SEED_IP,
        is_deleted=False,
        is_active=True,
    )
    session.add(mod)
    await session.flush()
    logger.info("Created module %s", name)
    return mod


async def _ensure_matrix(
    session: AsyncSession,
    roles_by_name: Dict[str, Role],
    modules_by_name: Dict[str, AppModule],
) -> None:
    for rname, mname, c, r, u, d in MATRIX:
        role = roles_by_name[rname]
        mod = modules_by_name[mname]
        q = await session.execute(
            select(ModuleRolePermission).where(
                ModuleRolePermission.role_id == role.id,
                ModuleRolePermission.module_id == mod.id,
                ModuleRolePermission.is_deleted == False,  # noqa: E712
            )
        )
        if q.scalar_one_or_none():
            continue
        session.add(
            ModuleRolePermission(
                module_id=mod.id,
                role_id=role.id,
                can_create=c,
                can_read=r,
                can_update=u,
                can_delete=d,
                created_by=ACTOR,
                created_ip=SEED_IP,
                is_deleted=False,
                is_active=True,
            )
        )
    await session.flush()
    logger.info("RBAC matrix rows ensured")


async def repair_rbac_matrix() -> None:
    """
    Upsert every row in ``MATRIX`` into ``M_module_role_permissions`` (no user/catalog changes).

    Use when ``/api/v1/auth/me/permissions`` returns empty ``menu_items`` / ``permissions`` for
    staff — usually a DB that was created without the seed matrix or where matrix rows were removed.
    """
    import os

    os.chdir(_ROOT)
    DatabaseConnection.initialize()
    factory = DatabaseConnection.get_session_factory()
    async with factory() as session:
        role_names = {r[0] for r in MATRIX}
        roles_by_name: Dict[str, Role] = {}
        for rname in sorted(role_names):
            row = await session.scalar(
                select(Role).where(Role.name == rname, Role.is_deleted == False)  # noqa: E712
            )
            if not row:
                logger.error("Missing role %r — create it or run full seed first.", rname)
                continue
            roles_by_name[rname] = row

        mod_names = {r[1] for r in MATRIX}
        modules_by_name: Dict[str, AppModule] = {}
        for mname in sorted(mod_names):
            row = await session.scalar(
                select(AppModule).where(AppModule.name == mname, AppModule.is_deleted == False)  # noqa: E712
            )
            if not row:
                logger.error("Missing module %r — create it or run full seed first.", mname)
                continue
            modules_by_name[mname] = row

        created = 0
        updated = 0
        for rname, mname, c, r, u, d in MATRIX:
            role = roles_by_name.get(rname)
            mod = modules_by_name.get(mname)
            if not role or not mod:
                continue
            mrp = await session.scalar(
                select(ModuleRolePermission).where(
                    ModuleRolePermission.role_id == role.id,
                    ModuleRolePermission.module_id == mod.id,
                )
            )
            if mrp:
                mrp.is_deleted = False
                mrp.is_active = True
                mrp.can_create = c
                mrp.can_read = r
                mrp.can_update = u
                mrp.can_delete = d
                updated += 1
            else:
                session.add(
                    ModuleRolePermission(
                        module_id=mod.id,
                        role_id=role.id,
                        can_create=c,
                        can_read=r,
                        can_update=u,
                        can_delete=d,
                        created_by=ACTOR,
                        created_ip=SEED_IP,
                        is_deleted=False,
                        is_active=True,
                    )
                )
                created += 1
        await session.commit()
    logger.info("repair_rbac_matrix done: created %s rows, updated %s rows", created, updated)


async def _truncate_all_app_tables() -> None:
    """
    Remove all rows from every table registered on ``Base`` (dev reset).

    PostgreSQL: single ``TRUNCATE ... CASCADE RESTART IDENTITY``.
    SQLite (in-memory tests): ``DELETE FROM`` each table in reverse FK order.
    """
    import app.db.models  # noqa: F401 — register all models on Base.metadata

    engine = DatabaseConnection.get_engine()
    dialect = engine.dialect.name
    tables = list(reversed(Base.metadata.sorted_tables))
    names = [f'"{t.name}"' for t in tables]

    async with engine.begin() as conn:
        if dialect == "postgresql":
            stmt = text(f"TRUNCATE {', '.join(names)} RESTART IDENTITY CASCADE")
            await conn.execute(stmt)
            logger.warning("Truncated all application tables (PostgreSQL).")
        elif dialect == "sqlite":
            for raw in names:
                await conn.execute(text(f"DELETE FROM {raw}"))
            logger.warning("Deleted all rows from application tables (SQLite).")
        else:
            raise RuntimeError(f"Unsupported dialect for --wipe-db: {dialect}")


async def _force_cleanup(session: AsyncSession) -> None:
    """Remove demo orders/items/payments and DEMO catalog/users (safe for re-seed)."""
    sub_orders = select(Order.id).where(Order.order_reference.like(f"{ORDER_REF_PREFIX}%"), Order.is_deleted == False)  # noqa: E712
    demo_med_ids = select(Medicine.id).where(Medicine.name.like(f"{DEMO_PREFIX} Med %"), Medicine.is_deleted == False)  # noqa: E712
    demo_off_ids = select(MedicineBrandOffering.id).where(MedicineBrandOffering.medicine_id.in_(demo_med_ids))
    demo_test_ids = select(PolyclinicTest.id).where(PolyclinicTest.name.like(f"{DEMO_PREFIX} %"), PolyclinicTest.is_deleted == False)  # noqa: E712
    demo_doc_ids = select(Doctor.id).where(Doctor.name.like(f"{DEMO_PREFIX} %"), Doctor.is_deleted == False)  # noqa: E712
    demo_coupon_ids = select(Coupon.id).where(Coupon.code.like("DEMO%"), Coupon.is_deleted == False)  # noqa: E712
    demo_emails = [e for e, _, _, _ in USER_SPECS]
    demo_user_ids = select(User.id).where(User.email.in_(demo_emails))
    notification_tables_ready = all(
        [
            await _table_exists(session, "M_notification_master"),
            await _table_exists(session, "M_notification_settings"),
            await _table_exists(session, "T_notification_logs"),
        ]
    )
    if notification_tables_ready:
        demo_notification_master_ids = select(NotificationMaster.id).where(
            NotificationMaster.event_code.like("DEMO_%"),
            NotificationMaster.is_deleted == False,  # noqa: E712
        )
        demo_notification_setting_ids = select(NotificationSetting.id).where(
            NotificationSetting.device_id.like("DEMO-%"),
            NotificationSetting.is_deleted == False,  # noqa: E712
        )

    await session.execute(delete(CouponUsage).where(CouponUsage.order_id.in_(sub_orders)))
    await session.execute(delete(CouponUsage).where(CouponUsage.coupon_id.in_(demo_coupon_ids)))
    await session.execute(delete(TestBooking).where(TestBooking.test_id.in_(demo_test_ids)))
    await session.execute(delete(Appointment).where(Appointment.doctor_id.in_(demo_doc_ids)))
    await session.execute(delete(Doctor).where(Doctor.id.in_(demo_doc_ids)))
    await session.execute(delete(PolyclinicTest).where(PolyclinicTest.id.in_(demo_test_ids)))
    await session.execute(delete(Address).where(Address.user_id.in_(demo_user_ids)))
    if notification_tables_ready:
        await session.execute(delete(NotificationLog).where(NotificationLog.notification_master_id.in_(demo_notification_master_ids)))
        await session.execute(delete(NotificationLog).where(NotificationLog.notification_setting_id.in_(demo_notification_setting_ids)))
        await session.execute(delete(NotificationSetting).where(NotificationSetting.id.in_(demo_notification_setting_ids)))
        await session.execute(delete(NotificationMaster).where(NotificationMaster.id.in_(demo_notification_master_ids)))

    await session.execute(delete(OrderItem).where(OrderItem.order_id.in_(sub_orders)))
    await session.execute(delete(OrderItem).where(OrderItem.medicine_brand_id.in_(demo_off_ids)))
    await session.execute(delete(Payment).where(Payment.order_id.in_(sub_orders)))
    await session.execute(delete(Order).where(Order.id.in_(sub_orders)))

    await session.execute(delete(InventoryAlert).where(InventoryAlert.medicine_brand_offering_id.in_(demo_off_ids)))
    await session.execute(delete(Inventory).where(Inventory.medicine_brand_offering_id.in_(demo_off_ids)))
    await session.execute(delete(MedicineBrandOffering).where(MedicineBrandOffering.id.in_(demo_off_ids)))
    await session.execute(delete(Medicine).where(Medicine.id.in_(demo_med_ids)))

    await session.execute(delete(Brand).where(Brand.name.like(f"{DEMO_PREFIX} Brand %"), Brand.is_deleted == False))  # noqa: E712
    await session.execute(
        delete(MedicineCategory).where(MedicineCategory.name.like(f"{DEMO_PREFIX} Cat %"), MedicineCategory.is_deleted == False)  # noqa: E712
    )

    await session.execute(delete(Coupon).where(Coupon.id.in_(demo_coupon_ids)))
    await session.execute(
        delete(DeliverySetting).where(
            DeliverySetting.delivery_zones.like("%__DEMO_SEED__%"),
            DeliverySetting.is_deleted == False,  # noqa: E712
        )
    )

    await session.execute(delete(User).where(User.email.in_(demo_emails)))
    await session.flush()
    logger.warning("Force cleanup removed DEMO-* rows across masters/transactions and %s* orders.", ORDER_REF_PREFIX)


async def _seed_notifications(
    session: AsyncSession,
    admin_id: UUID,
    customer: User,
) -> None:
    """Seed notification masters/settings/logs for admin web notification screens."""
    tables_ready = all(
        [
            await _table_exists(session, "M_notification_master"),
            await _table_exists(session, "M_notification_settings"),
            await _table_exists(session, "T_notification_logs"),
        ]
    )
    if not tables_ready:
        logger.warning("Notification tables not present yet; skipping notification seed rows.")
        return
    template = {
        "push": {
            "title_template": "Order {{order_reference}} update",
            "body_template": "Hi {{customer_name}}, your order is now {{order_status}}.",
            "message_variables": ["order_reference", "customer_name", "order_status"],
            "is_enabled": True,
        },
        "sms": {
            "title_template": "",
            "body_template": "Order {{order_reference}} is {{order_status}}.",
            "message_variables": ["order_reference", "order_status"],
            "is_enabled": False,
        },
    }
    masters_data: List[Tuple[str, str, str]] = [
        ("DEMO_ORDER_PLACED", "Order placed", "Sent after successful payment"),
        ("DEMO_ORDER_OUT_FOR_DELIVERY", "Out for delivery", "Sent when parcel is with delivery agent"),
        ("DEMO_ORDER_DELIVERED", "Order delivered", "Sent on successful delivery"),
    ]
    masters: List[NotificationMaster] = []
    for event_code, event_name, description in masters_data:
        row = await session.scalar(
            select(NotificationMaster).where(
                NotificationMaster.event_code == event_code,
                NotificationMaster.is_deleted == False,  # noqa: E712
            )
        )
        if not row:
            row = NotificationMaster(
                event_code=event_code,
                event_name=event_name,
                description=description,
                channel_templates=json.dumps(template),
                created_by=admin_id,
                created_ip=SEED_IP,
                is_deleted=False,
                is_active=True,
            )
            session.add(row)
            await session.flush()
        masters.append(row)

    setting = await session.scalar(
        select(NotificationSetting).where(
            NotificationSetting.user_id == customer.id,
            NotificationSetting.device_id == "DEMO-ANDROID-01",
            NotificationSetting.is_deleted == False,  # noqa: E712
        )
    )
    if not setting:
        setting = NotificationSetting(
            user_id=customer.id,
            device_id="DEMO-ANDROID-01",
            device_platform="android",
            expo_push_token="ExponentPushToken[DEMO-SEED-TOKEN-01]",
            is_push_enabled=True,
            created_by=admin_id,
            created_ip=SEED_IP,
            is_deleted=False,
            is_active=True,
        )
        session.add(setting)
        await session.flush()

    existing_log = await session.scalar(
        select(NotificationLog.id).where(
            NotificationLog.expo_push_token == "ExponentPushToken[DEMO-SEED-TOKEN-01]",
            NotificationLog.is_deleted == False,  # noqa: E712
        )
    )
    if not existing_log:
        for idx, status in enumerate(["sent", "failed", "retrying"], start=1):
            session.add(
                NotificationLog(
                    user_id=customer.id,
                    notification_master_id=masters[min(idx - 1, len(masters) - 1)].id,
                    notification_setting_id=setting.id,
                    channel="push",
                    expo_push_token="ExponentPushToken[DEMO-SEED-TOKEN-01]",
                    payload_snapshot='{"order_reference":"DEMO-SEED-0%d"}' % idx,
                    send_status=status,
                    provider_response='{"status":"ok"}' if status == "sent" else None,
                    error_message=None if status == "sent" else "Expo push service transient error",
                    retry_count=0 if status == "sent" else 1,
                    max_retry_attempts=3,
                    retry_interval_minutes=5,
                    next_retry_at=_now() + timedelta(minutes=5) if status == "retrying" else None,
                    sent_at=_now() if status == "sent" else None,
                    created_by=admin_id,
                    created_ip=SEED_IP,
                    is_deleted=False,
                )
            )
    await session.flush()
    logger.info("Notification demo rows ensured")


async def _seed_users(session: AsyncSession, pwd_hash: str, roles_by_name: Dict[str, Role]) -> Dict[str, User]:
    """Create demo users; first user (admin) self-references created_by."""
    out: Dict[str, User] = {}
    admin_role = roles_by_name["ADMIN"]
    admin = User(
        role_id=admin_role.id,
        full_name="Demo Admin",
        mobile_number="9999999901",
        email="admin@newbalan.com",
        password_hash=pwd_hash,
        created_by=ACTOR,
        created_ip=SEED_IP,
        is_deleted=False,
        is_active=True,
    )
    session.add(admin)
    await session.flush()
    admin.created_by = admin.id
    await session.flush()
    out["admin@newbalan.com"] = admin

    for email, role_name, full_name, mobile in USER_SPECS[1:]:
        role = roles_by_name[role_name]
        u = User(
            role_id=role.id,
            full_name=full_name,
            mobile_number=mobile,
            email=email,
            password_hash=pwd_hash,
            created_by=admin.id,
            created_ip=SEED_IP,
            is_deleted=False,
            is_active=True,
        )
        session.add(u)
        await session.flush()
        out[email] = u
        logger.info("Created user %s", email)

    return out


async def _seed_catalog(session: AsyncSession, admin_id: UUID) -> Tuple[List[MedicineCategory], List[Brand], List[MedicineBrandOffering]]:
    cats: List[MedicineCategory] = []
    for i in range(1, 5):
        c = MedicineCategory(
            name=f"{DEMO_PREFIX} Cat {i}",
            description=f"Demo therapeutic category {i}",
            created_by=admin_id,
            created_ip=SEED_IP,
            is_deleted=False,
            is_active=True,
        )
        session.add(c)
        cats.append(c)
    await session.flush()

    brands: List[Brand] = []
    for i in range(1, 5):
        b = Brand(
            name=f"{DEMO_PREFIX} Brand {i}",
            description=f"Demo manufacturer line {i}",
            created_by=admin_id,
            created_ip=SEED_IP,
            is_deleted=False,
            is_active=True,
        )
        session.add(b)
        brands.append(b)
    await session.flush()

    offerings: List[MedicineBrandOffering] = []
    med_names = [
        "Paracetamol 500",
        "Amoxicillin 250",
        "Azithromycin 500",
        "Omeprazole 20",
        "Cetirizine 10",
        "Metformin 500",
        "Atorvastatin 10",
        "Salbutamol Inhaler",
        "Diclofenac Gel",
        "ORS Sachet",
    ]
    for idx, med_name in enumerate(med_names):
        m = Medicine(
            medicine_category_id=cats[idx % 4].id,
            name=f"{DEMO_PREFIX} Med {med_name}",
            is_prescription_required=idx % 3 == 0,
            description=f"Demo SKU {idx + 1}",
            is_available=True,
            created_by=admin_id,
            created_ip=SEED_IP,
            is_deleted=False,
            is_active=True,
        )
        session.add(m)
        await session.flush()
        brand = brands[idx % 4]
        off = MedicineBrandOffering(
            medicine_id=m.id,
            brand_id=brand.id,
            manufacturer=f"{DEMO_PREFIX} Pharma Ltd",
            mrp=Decimal("120.00") + Decimal(idx * 11),
            description=None,
            is_available=True,
            created_by=admin_id,
            created_ip=SEED_IP,
            is_deleted=False,
            is_active=True,
        )
        session.add(off)
        await session.flush()
        inv = Inventory(
            medicine_brand_offering_id=off.id,
            stock_quantity=500,
            created_by=admin_id,
            created_ip=SEED_IP,
            is_deleted=False,
            is_active=True,
        )
        session.add(inv)
        offerings.append(off)

    await session.flush()
    logger.info("Catalog: 4 categories, 4 brands, %s medicines + offerings + inventory", len(offerings))
    return cats, brands, offerings


async def _seed_delivery_settings(session: AsyncSession, admin_id: UUID) -> None:
    """One demo delivery row (marker in ``delivery_zones`` for ``--force`` cleanup)."""
    q = await session.execute(
        select(DeliverySetting).where(
            DeliverySetting.delivery_zones.like("%__DEMO_SEED__%"),
            DeliverySetting.is_deleted == False,  # noqa: E712
        )
    )
    if q.scalar_one_or_none():
        return
    session.add(
        DeliverySetting(
            is_enabled=True,
            min_order_amount=Decimal("199.00"),
            delivery_fee=Decimal("40.00"),
            free_delivery_threshold=Decimal("799.00"),
            free_delivery_max_amount=Decimal("80.00"),
            delivery_zones='[{"city":"Chennai","pincodes":["600001","600002"],"__DEMO_SEED__":true}]',
            show_marquee=True,
            delivery_slot_times='["09:00-12:00","14:00-18:00","18:00-21:00"]',
            created_by=admin_id,
            created_ip=SEED_IP,
            is_deleted=False,
            is_active=True,
        )
    )
    await session.flush()
    logger.info("Delivery settings (demo) ensured")


async def _seed_doctors_and_appointments(session: AsyncSession, admin_id: UUID) -> Tuple[List[Doctor], List[Appointment]]:
    specs: List[Tuple[str, str, str, str]] = [
        (f"{DEMO_PREFIX} Dr. Ananya Rao", "General Medicine", "MBBS, MD", "demo.doctor1@newbalan.com"),
        (f"{DEMO_PREFIX} Dr. Vikram Singh", "Cardiology", "DM Cardio", "demo.doctor2@newbalan.com"),
        (f"{DEMO_PREFIX} Dr. Meera Iyer", "Pediatrics", "MBBS, DCH", "demo.doctor3@newbalan.com"),
    ]
    doctors: List[Doctor] = []
    for name, spec, qual, demail in specs:
        d = Doctor(
            name=name,
            specialty=spec,
            qualifications=qual,
            phone="9876500001",
            email=demail,
            consultation_fee=Decimal("500.00"),
            morning_start=time(9, 0),
            morning_end=time(13, 0),
            evening_start=time(17, 0),
            evening_end=time(20, 0),
            created_by=admin_id,
            created_ip=SEED_IP,
            is_deleted=False,
            is_active=True,
        )
        session.add(d)
        doctors.append(d)
    await session.flush()

    today = _now().date()
    appts: List[Appointment] = []
    rows = [
        (0, "Demo Patient One", "9888877701", today + timedelta(days=1), time(10, 30), "PENDING", "First consult"),
        (1, "Demo Patient Two", "9888877702", today + timedelta(days=2), time(11, 0), "CONFIRMED", None),
        (2, "Demo Customer", "9999999905", today + timedelta(days=3), None, "PENDING", "Walk-in query"),
        (0, "Demo Patient Three", "9888877703", today + timedelta(days=5), time(9, 0), "CANCELLED", "Rescheduled"),
    ]
    for doc_i, pname, phone, adate, atime, st, msg in rows:
        appts.append(
            Appointment(
                doctor_id=doctors[doc_i].id,
                patient_name=pname,
                patient_phone=phone,
                appointment_date=adate,
                appointment_time=atime,
                status=st,
                message=msg,
                created_by=admin_id,
                created_ip=SEED_IP,
                is_deleted=False,
            )
        )
    session.add_all(appts)
    await session.flush()
    logger.info("Doctors + appointments: %s doctors, %s appointments", len(doctors), len(appts))
    return doctors, appts


async def _seed_polyclinic_and_bookings(session: AsyncSession, admin_id: UUID) -> Tuple[List[PolyclinicTest], List[TestBooking]]:
    test_rows: List[Tuple[str, str, Decimal, str, bool, str]] = [
        (f"{DEMO_PREFIX} Complete Blood Count", "CBC — red/white cells, platelets", Decimal("450.00"), "Same day", False, "TestTube"),
        (f"{DEMO_PREFIX} Lipid Profile", "Cholesterol panel", Decimal("620.00"), "Fasting 10h", True, "Activity"),
        (f"{DEMO_PREFIX} Thyroid Panel", "TSH, T3, T4", Decimal("890.00"), "Same day", False, "Zap"),
        (f"{DEMO_PREFIX} HbA1c", "3-month glucose average", Decimal("380.00"), "Same day", False, "Gauge"),
    ]
    tests: List[PolyclinicTest] = []
    for name, desc, price, dur, fast, icon in test_rows:
        t = PolyclinicTest(
            name=name,
            description=desc,
            price=price,
            duration=dur,
            fasting_required=fast,
            icon_name=icon,
            created_by=admin_id,
            created_ip=SEED_IP,
            is_deleted=False,
            is_active=True,
        )
        session.add(t)
        tests.append(t)
    await session.flush()

    today = _now().date()
    bookings: List[TestBooking] = [
        TestBooking(
            test_id=tests[0].id,
            patient_name="Demo Lab Patient A",
            patient_phone="9777766601",
            booking_date=today + timedelta(days=1),
            booking_time="09:30",
            status="PENDING",
            notes="Home sample preferred",
            created_by=admin_id,
            created_ip=SEED_IP,
            is_deleted=False,
        ),
        TestBooking(
            test_id=tests[1].id,
            patient_name="Demo Lab Patient B",
            patient_phone="9777766602",
            booking_date=today + timedelta(days=2),
            booking_time="07:00",
            status="CONFIRMED",
            notes=None,
            created_by=admin_id,
            created_ip=SEED_IP,
            is_deleted=False,
        ),
        TestBooking(
            test_id=tests[2].id,
            patient_name="Demo Customer",
            patient_phone="9999999905",
            booking_date=today + timedelta(days=4),
            booking_time=None,
            status="PENDING",
            notes=None,
            created_by=admin_id,
            created_ip=SEED_IP,
            is_deleted=False,
        ),
    ]
    session.add_all(bookings)
    await session.flush()
    logger.info("Polyclinic: %s tests, %s test bookings", len(tests), len(bookings))
    return tests, bookings


async def _seed_coupons(session: AsyncSession, admin_id: UUID) -> Dict[str, Coupon]:
    """Unique codes starting with DEMO (cleaned up by ``--force``)."""
    specs: List[Tuple[str, Decimal, date | None, Decimal | None, Decimal | None, int | None, bool]] = [
        ("DEMO10", Decimal("10.00"), date(2030, 12, 31), Decimal("100.00"), Decimal("75.00"), 500, False),
        ("DEMO15", Decimal("15.00"), date(2030, 12, 31), Decimal("250.00"), Decimal("120.00"), None, False),
        ("DEMOFIRST", Decimal("20.00"), date(2030, 6, 1), Decimal("0.00"), Decimal("200.00"), 100, True),
    ]
    out: Dict[str, Coupon] = {}
    for code, pct, exp, min_amt, max_disc, limit, first_only in specs:
        existing = await session.scalar(select(Coupon).where(Coupon.code == code, Coupon.is_deleted == False))  # noqa: E712
        if existing:
            out[code] = existing
            continue
        c = Coupon(
            code=code,
            discount_percentage=pct,
            expiry_date=exp,
            min_order_amount=min_amt,
            max_discount_amount=max_disc,
            usage_limit=limit,
            usage_count=0,
            first_order_only=first_only,
            created_by=admin_id,
            created_ip=SEED_IP,
            is_deleted=False,
            is_active=True,
        )
        session.add(c)
        await session.flush()
        out[code] = c
    await session.flush()
    logger.info("Coupons: %s codes", ", ".join(out.keys()))
    return out


async def _seed_customer_addresses(session: AsyncSession, admin_id: UUID, customer_id: UUID) -> None:
    session.add_all(
        [
            Address(
                user_id=customer_id,
                label="Home",
                street=f"{DEMO_PREFIX} 12, Lake View Road, Adyar",
                city="Chennai",
                state="Tamil Nadu",
                pincode="600020",
                country="India",
                is_default=True,
                created_by=admin_id,
                created_ip=SEED_IP,
                is_deleted=False,
                is_active=True,
            ),
            Address(
                user_id=customer_id,
                label="Office",
                street=f"{DEMO_PREFIX} IT Park, Phase 2, OMR",
                city="Chennai",
                state="Tamil Nadu",
                pincode="600097",
                country="India",
                is_default=False,
                created_by=admin_id,
                created_ip=SEED_IP,
                is_deleted=False,
                is_active=True,
            ),
        ]
    )
    await session.flush()
    logger.info("Customer saved addresses: 2 rows")


async def _seed_inventory_alert_demo(session: AsyncSession, admin_id: UUID, offerings: List[MedicineBrandOffering]) -> None:
    """One offering below ``INV_STOCK_THRESHOLD`` (10) with matching ``T_inventory_alerts`` row."""
    if not offerings:
        return
    off0 = offerings[0]
    inv_row = (
        await session.execute(
            select(Inventory).where(
                Inventory.medicine_brand_offering_id == off0.id,
                Inventory.is_deleted == False,  # noqa: E712
            )
        )
    ).scalar_one()
    inv_row.stock_quantity = 5
    existing = await session.scalar(
        select(InventoryAlert).where(
            InventoryAlert.medicine_brand_offering_id == off0.id,
            InventoryAlert.is_deleted == False,  # noqa: E712
        )
    )
    if not existing:
        session.add(
            InventoryAlert(
                medicine_brand_offering_id=off0.id,
                current_stock=5,
                created_by=admin_id,
                created_ip=SEED_IP,
                is_deleted=False,
            )
        )
    await session.flush()
    logger.info("Inventory alert demo: offering %s stock=5", off0.id)


async def _seed_coupon_usages(session: AsyncSession, admin_id: UUID, customer: User, coupon_by_code: Dict[str, Coupon]) -> None:
    order = await session.scalar(
        select(Order).where(Order.order_reference == f"{ORDER_REF_PREFIX}05", Order.is_deleted == False)  # noqa: E712
    )
    if not order:
        return
    c10 = coupon_by_code.get("DEMO10")
    if not c10:
        return
    exists = await session.scalar(
        select(CouponUsage.id).where(
            CouponUsage.order_id == order.id,
            CouponUsage.coupon_id == c10.id,
            CouponUsage.is_deleted == False,  # noqa: E712
        )
    )
    if exists:
        return
    session.add(
        CouponUsage(
            coupon_id=c10.id,
            order_id=order.id,
            customer_id=customer.id,
            discount_amount=Decimal("25.00"),
            coupon_code=c10.code,
            customer_name=customer.full_name,
            customer_phone=customer.mobile_number,
            order_final_amount=order.final_amount,
            created_by=admin_id,
            created_ip=SEED_IP,
            is_deleted=False,
        )
    )
    c10.usage_count = (c10.usage_count or 0) + 1
    await session.flush()
    logger.info("Coupon usage: DEMO10 linked to %s05", ORDER_REF_PREFIX)


def _order_statuses_20() -> List[str]:
    """Varied lifecycle statuses for 20 demo orders."""
    return [
        lc.PAYMENT_PENDING,
        lc.PAYMENT_PENDING,
        lc.PAYMENT_CANCELLED,
        lc.ORDER_RECEIVED,
        lc.ORDER_TAKEN,
        lc.ORDER_PROCESSING,
        lc.DELIVERY_ASSIGNED,
        lc.PARCEL_TAKEN,
        lc.OUT_FOR_DELIVERY,
        lc.DELIVERED,
        lc.CANCELLED_BY_STAFF,
        lc.DELIVERY_RETURNED,
        lc.REFUND_INITIATED,
        lc.REFUNDED,
        lc.ORDER_RECEIVED,
        lc.ORDER_PROCESSING,
        lc.DELIVERED,
        lc.PAYMENT_PENDING,
        lc.ORDER_TAKEN,
        lc.OUT_FOR_DELIVERY,
    ]


async def _seed_orders(
    session: AsyncSession,
    admin_id: UUID,
    customer: User,
    delivery_agent: User,
    offerings: List[MedicineBrandOffering],
) -> None:
    statuses = _order_statuses_20()
    base = _now()
    for i in range(20):
        n = i + 1
        ref = f"{ORDER_REF_PREFIX}{n:02d}"
        st = statuses[i]
        total = Decimal("250.00") + Decimal(n * 5)
        disc = Decimal("0.00") if n % 4 else Decimal("25.00")
        delivery_fee = Decimal("40.00")
        final_am = total - disc + delivery_fee

        extra: Dict[str, Any] = {}
        if st not in (lc.PAYMENT_PENDING, lc.PAYMENT_CANCELLED):
            extra["payment_completed_at"] = base - timedelta(hours=30 - n)
        if st in (
            lc.ORDER_RECEIVED,
            lc.ORDER_TAKEN,
            lc.ORDER_PROCESSING,
            lc.DELIVERY_ASSIGNED,
            lc.PARCEL_TAKEN,
            lc.OUT_FOR_DELIVERY,
            lc.DELIVERED,
            lc.DELIVERY_RETURNED,
            lc.REFUND_INITIATED,
            lc.REFUNDED,
            lc.CANCELLED_BY_STAFF,
        ):
            extra["order_received_at"] = extra.get("payment_completed_at") or base - timedelta(hours=28 - n)
        if st in (lc.ORDER_TAKEN, lc.ORDER_PROCESSING, lc.DELIVERY_ASSIGNED, lc.PARCEL_TAKEN, lc.OUT_FOR_DELIVERY, lc.DELIVERED):
            extra["order_packed_at"] = base - timedelta(hours=24 - n)
        if st in (lc.DELIVERY_ASSIGNED, lc.PARCEL_TAKEN, lc.OUT_FOR_DELIVERY, lc.DELIVERED, lc.DELIVERY_RETURNED):
            extra["delivery_assigned_user_id"] = delivery_agent.id
            extra["delivery_assigned_at"] = base - timedelta(hours=20 - n)
        if st in (lc.DELIVERED,):
            extra["delivered_at"] = base - timedelta(hours=4)
        if st == lc.CANCELLED_BY_STAFF:
            extra["cancellation_reason"] = "Demo staff cancellation"
            extra["cancelled_by_user_id"] = admin_id
            extra["cancelled_at"] = base - timedelta(hours=10)
        if st == lc.DELIVERY_RETURNED:
            extra["return_reason"] = "Customer refused demo delivery"

        order = Order(
            order_reference=ref,
            customer_id=customer.id,
            customer_name=customer.full_name,
            customer_phone=customer.mobile_number,
            customer_email=customer.email,
            delivery_address=f"{DEMO_PREFIX} Address line 1, Chennai {n}",
            pincode="600001",
            city="Chennai",
            order_status=st,
            total_amount=total,
            discount_amount=disc,
            delivery_fee=delivery_fee,
            final_amount=final_am,
            payment_method="RAZORPAY",
            notes=f"Demo order {n} ({st})",
            created_by=admin_id,
            created_ip=SEED_IP,
            is_deleted=False,
            **extra,
        )
        session.add(order)
        await session.flush()

        off = offerings[i % len(offerings)]
        qty = 1 + (n % 3)
        unit = Decimal("55.00")
        oi = OrderItem(
            order_id=order.id,
            medicine_brand_id=off.id,
            medicine_name=f"{DEMO_PREFIX} item med",
            brand_name=f"{DEMO_PREFIX} item brand",
            quantity=qty,
            unit_price=unit,
            total_price=unit * qty,
            requires_prescription=False,
            created_by=admin_id,
            created_ip=SEED_IP,
            is_deleted=False,
        )
        session.add(oi)

        if st not in (lc.PAYMENT_PENDING, lc.PAYMENT_CANCELLED) and st != lc.CANCELLED_BY_STAFF:
            pay = Payment(
                order_id=order.id,
                payment_method="RAZORPAY",
                payment_status="COMPLETED",
                amount=final_am,
                payment_date=extra.get("payment_completed_at") or base,
                created_by=admin_id,
                created_ip=SEED_IP,
                is_deleted=False,
                refund_status="NONE",
                refund_amount=Decimal("0"),
            )
            session.add(pay)

    await session.flush()
    logger.info("Created 20 demo orders (%s..)", ORDER_REF_PREFIX)


async def run(force: bool, create_tables: bool, wipe_db: bool) -> None:
    import os

    os.chdir(_ROOT)
    DatabaseConnection.initialize()
    # Wipe requires every ORM table to exist, or PostgreSQL TRUNCATE fails on missing names.
    if create_tables or wipe_db:
        await DatabaseConnection.create_tables()

    engine = DatabaseConnection.get_engine()
    if engine.dialect.name == "postgresql":
        async with engine.begin() as conn:
            from app.db.order_fulfillment_schema import apply_order_fulfillment_schema

            await apply_order_fulfillment_schema(conn)

    if wipe_db:
        await _truncate_all_app_tables()

    factory = DatabaseConnection.get_session_factory()
    pwd_hash = hash_password(PLAIN_PASSWORD)

    async with factory() as session:
        incremental_only = False
        if not wipe_db and not force:
            existing = await session.scalar(
                select(User.id).where(User.email == "admin@newbalan.com", User.is_deleted == False)  # noqa: E712
            )
            if existing:
                incremental_only = True
                logger.info("Demo users already present. Running incremental seed for modules/RBAC/notifications.")

        if force and not wipe_db:
            await _force_cleanup(session)

        roles_by_name: Dict[str, Role] = {}
        for name, desc in ROLE_ROWS:
            roles_by_name[name] = await _get_or_create_role(session, name, desc)

        modules_by_name: Dict[str, AppModule] = {}
        for name, dname, ord_, icon in MODULE_ROWS:
            modules_by_name[name] = await _get_or_create_module(session, name, dname, ord_, icon)

        omod = modules_by_name.get("orders")
        if omod is not None and int(omod.display_order or 0) != 1:
            omod.display_order = 1
            await session.flush()
            logger.info("orders: display_order set to 1 (default staff landing tab)")

        await _ensure_matrix(session, roles_by_name, modules_by_name)

        if incremental_only:
            admin = await session.scalar(
                select(User).where(User.email == "admin@newbalan.com", User.is_deleted == False)  # noqa: E712
            )
            customer = await session.scalar(
                select(User).where(User.email == "customer@newbalan.com", User.is_deleted == False)  # noqa: E712
            )
            if admin and customer:
                await _seed_notifications(session, admin.id, customer)
            await session.commit()
            logger.info("Incremental seed complete.")
            return

        users = await _seed_users(session, pwd_hash, roles_by_name)
        admin = users["admin@newbalan.com"]
        customer = users["customer@newbalan.com"]
        delivery = users["deliveryagent@newbalan.com"]

        _, _, offerings = await _seed_catalog(session, admin.id)
        await _seed_delivery_settings(session, admin.id)
        await _seed_doctors_and_appointments(session, admin.id)
        await _seed_polyclinic_and_bookings(session, admin.id)
        coupon_by_code = await _seed_coupons(session, admin.id)
        await _seed_customer_addresses(session, admin.id, customer.id)
        await _seed_inventory_alert_demo(session, admin.id, offerings)
        await _seed_orders(session, admin.id, customer, delivery, offerings)
        await _seed_coupon_usages(session, admin.id, customer, coupon_by_code)
        await _seed_notifications(session, admin.id, customer)

        await session.commit()

    logger.info("Seed complete. Log in with any @newbalan.com user / %s", PLAIN_PASSWORD)


def main() -> None:
    p = argparse.ArgumentParser(description="Seed RBAC, demo users, catalog, and orders.")
    p.add_argument("--force", action="store_true", help="Delete previous DEMO-* seed rows and re-insert.")
    p.add_argument(
        "--wipe-db",
        action="store_true",
        help="Truncate ALL application tables (PostgreSQL TRUNCATE CASCADE), then insert fresh seed data.",
    )
    p.add_argument(
        "--create-tables",
        action="store_true",
        help="Run SQLAlchemy create_all first (empty local DB).",
    )
    p.add_argument(
        "--repair-rbac",
        action="store_true",
        help="Upsert M_module_role_permissions from MATRIX only (fixes empty menu for ADMIN and other roles).",
    )
    args = p.parse_args()
    if args.repair_rbac:
        if any([args.wipe_db, args.force, args.create_tables]):
            logger.warning("With --repair-rbac, other flags are ignored.")
        asyncio.run(repair_rbac_matrix())
        return
    if args.wipe_db and args.force:
        logger.warning("--wipe-db already clears all tables; --force is redundant.")
    asyncio.run(run(args.force, args.create_tables, args.wipe_db))


if __name__ == "__main__":
    main()
