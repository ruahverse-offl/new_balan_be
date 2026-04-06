"""
Seed PostgreSQL with RBAC, users (admin / dev / customer), menu tasks, and sample master + transaction data.

Run from the backend project root (folder containing `app/`):

    python Scripts/seed_database.py

Options:

    --reset     TRUNCATE all application tables (CASCADE) then seed (destructive).
    --password  Default password for seeded users (default: NewBalan@2026)

Requires DATABASE_URL and existing schema. On startup the API runs `create_all` plus idempotent
PostgreSQL patches (e.g. T_orders fulfillment columns). Or: `python Scripts/seed_database.py` which
calls the same table setup.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import date, datetime, time, timezone
from decimal import Decimal
from uuid import UUID, uuid4

# Project root = parent of Scripts/
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from sqlalchemy import text, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import DatabaseConnection
from app.db.models import (
    Role,
    Permission,
    RolePermission,
    MenuTask,
    RoleTaskGrant,
    User,
    MedicineCategory,
    Brand,
    Medicine,
    MedicineBrandOffering,
    Inventory,
    Order,
    OrderItem,
    Payment,
    Doctor,
    Appointment,
    PolyclinicTest,
    TestBooking,
    Coupon,
    CouponUsage,
    DeliverySetting,
    Address,
)
from app.utils.password import hash_password

# Audit placeholder for seed rows (no real user yet)
SEED_ACTOR = UUID("00000000-0000-0000-0000-000000000001")
SEED_IP = "127.0.0.1"

DEFAULT_PASSWORD = "NewBalan@2026"

# Full permission catalog (aligned with routers + frontend permissionMapper)
PERMISSION_CODES = sorted(
    {
        # RBAC (DEV role gets only these)
        "ROLE_CREATE",
        "ROLE_VIEW",
        "ROLE_UPDATE",
        "ROLE_DELETE",
        "PERMISSION_CREATE",
        "PERMISSION_VIEW",
        "PERMISSION_UPDATE",
        "PERMISSION_DELETE",
        "ROLE_PERMISSION_CREATE",
        "ROLE_PERMISSION_VIEW",
        "ROLE_PERMISSION_UPDATE",
        "ROLE_PERMISSION_DELETE",
        # Operational
        "DASHBOARD_VIEW",
        "DASHBOARD_ANALYTICS",
        "DOCTOR_VIEW",
        "DOCTOR_CREATE",
        "DOCTOR_UPDATE",
        "DOCTOR_DELETE",
        "MEDICINE_VIEW",
        "MEDICINE_CREATE",
        "MEDICINE_UPDATE",
        "MEDICINE_DELETE",
        "MEDICINE_CATEGORY_MANAGE",
        "ORDER_CREATE",
        "ORDER_VIEW",
        "ORDER_UPDATE",
        "ORDER_DETAIL_VIEW",
        "ORDER_CANCEL",
        "DELIVERY_ORDER_VIEW",
        "DELIVERY_ORDER_UPDATE",
        "PAYMENT_PROCESS",
        "APPOINTMENT_VIEW",
        "APPOINTMENT_CREATE",
        "APPOINTMENT_UPDATE",
        "APPOINTMENT_DELETE",
        "APPOINTMENT_STATUS_UPDATE",
        "DELIVERY_SETTINGS_VIEW",
        "DELIVERY_SETTINGS_UPDATE",
        "DELIVERY_SLOT_MANAGE",
        "COUPON_VIEW",
        "COUPON_CREATE",
        "COUPON_UPDATE",
        "COUPON_DELETE",
        "COUPON_MARQUEE_MANAGE",
        "STAFF_VIEW",
        "STAFF_CREATE",
        "STAFF_UPDATE",
        "STAFF_DELETE",
        "STAFF_PERMISSIONS_MANAGE",
        "INVENTORY_VIEW",
        "INVENTORY_UPDATE",
        "PRESCRIPTION_APPROVE",
        "PRESCRIPTION_REVIEW",
    }
)

RBAC_ONLY_CODES = {
    "ROLE_CREATE",
    "ROLE_VIEW",
    "ROLE_UPDATE",
    "ROLE_DELETE",
    "PERMISSION_CREATE",
    "PERMISSION_VIEW",
    "PERMISSION_UPDATE",
    "PERMISSION_DELETE",
    "ROLE_PERMISSION_CREATE",
    "ROLE_PERMISSION_VIEW",
    "ROLE_PERMISSION_UPDATE",
    "ROLE_PERMISSION_DELETE",
}

ROLES_SPEC = [
    ("ADMIN", "Full application access (operations + RBAC)."),
    ("DEV", "RBAC only — roles, permissions, role-permission links."),
    ("DELIVERY", "Delivery agent — assigned orders only (view + status updates)."),
    ("CUSTOMER", "Storefront customer; no admin permissions."),
]

USERS_SPEC = [
    ("admin@newbalan.com", "Admin User", "ADMIN", "9999999999"),
    ("dev@newbalan.com", "Dev User", "DEV", "9999999998"),
    ("delivery@newbalan.com", "Delivery Agent", "DELIVERY", "9999999996"),
    ("customer@newbalan.com", "Customer User", "CUSTOMER", "9999999997"),
]

# Admin sidebar tasks (codes match React admin tab ids; icon_key matches ADMIN_SIDEBAR_ICON_MAP)
MENU_TASKS_SPEC: list[tuple[str, str, int, str | None]] = [
    ("dashboard", "Statistics", 0, "LayoutDashboard"),
    ("roles-access", "Roles & access", 5, "Shield"),
    ("doctors", "Manage Doctors", 10, "Users"),
    ("medicines", "Manage Medicines", 20, "Pill"),
    ("therapeutic-categories", "Medicine Cat.", 25, "Tags"),
    ("inventory", "Inventory", 26, "Package"),
    ("brand-master", "Brand catalog", 27, "Tag"),
    ("orders", "Orders", 30, "ShoppingCart"),
    ("appointments", "Appointments", 40, "Clock"),
    ("delivery", "Delivery Settings", 50, "Truck"),
    ("coupons", "Coupons & Marquee", 60, "Ticket"),
    ("staff", "Manage Staff", 70, "UserCheck"),
    ("test-bookings", "Test Bookings", 80, "Calendar"),
    ("payments", "Payments", 90, "CreditCard"),
    ("coupon-usages", "Coupon Usages", 100, "BarChart3"),
]

# DEV: dashboard + staff (typical place for user/role tooling); extend if your UI differs
DEV_MENU_CODES = frozenset({"dashboard", "staff", "roles-access"})


async def _truncate_all(session: AsyncSession) -> None:
    """Clear app tables (PostgreSQL)."""
    tables = [
        "T_order_items",
        "T_payments",
        "T_coupon_usages",
        "T_orders",
        "T_appointments",
        "T_test_bookings",
        "T_inventory_alerts",
        "M_inventory",
        "M_role_task_grants",
        "M_menu_tasks",
        "M_addresses",
        "M_users",
        "M_medicine_brand_offerings",
        "M_medicines",
        "M_brands",
        "M_medicine_categories",
        "M_doctors",
        "M_polyclinic_tests",
        "M_coupons",
        "M_delivery_settings",
        "M_role_permissions",
        "M_permissions",
        "M_roles",
    ]
    quoted = ", ".join(f'"{t}"' for t in tables)
    await session.execute(text(f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE"))


async def seed(session: AsyncSession, password_plain: str) -> None:
    pw_hash = hash_password(password_plain)

    # --- Roles ---
    role_ids: dict[str, UUID] = {}
    for name, desc in ROLES_SPEC:
        rid = uuid4()
        role_ids[name] = rid
        session.add(
            Role(
                id=rid,
                name=name,
                description=desc,
                created_by=SEED_ACTOR,
                created_ip=SEED_IP,
            )
        )

    # --- Permissions ---
    perm_ids: dict[str, UUID] = {}
    for code in PERMISSION_CODES:
        pid = uuid4()
        perm_ids[code] = pid
        session.add(
            Permission(
                id=pid,
                code=code,
                description=f"Permission: {code}",
                created_by=SEED_ACTOR,
                created_ip=SEED_IP,
            )
        )

    # --- Role permissions ---
    def grant_for_role(role_name: str) -> set[str]:
        if role_name == "ADMIN":
            return set(PERMISSION_CODES)
        if role_name == "DEV":
            return set(RBAC_ONLY_CODES)
        if role_name == "DELIVERY":
            return {"DELIVERY_ORDER_VIEW", "DELIVERY_ORDER_UPDATE"}
        return set()

    for rname, _ in ROLES_SPEC:
        for code in grant_for_role(rname):
            if code not in perm_ids:
                continue
            session.add(
                RolePermission(
                    id=uuid4(),
                    role_id=role_ids[rname],
                    permission_id=perm_ids[code],
                    created_by=SEED_ACTOR,
                    created_ip=SEED_IP,
                )
            )

    await session.flush()

    # --- Users (depend on roles) ---
    user_ids: dict[str, UUID] = {}
    for email, full_name, rname, mobile in USERS_SPEC:
        uid = uuid4()
        user_ids[email] = uid
        session.add(
            User(
                id=uid,
                role_id=role_ids[rname],
                full_name=full_name,
                mobile_number=mobile,
                email=email,
                password_hash=pw_hash,
                created_by=SEED_ACTOR,
                created_ip=SEED_IP,
            )
        )

    await session.flush()

    admin_id = user_ids["admin@newbalan.com"]

    # --- Menu tasks + grants ---
    task_ids: dict[str, UUID] = {}
    for code, label, sort_o, icon_k in MENU_TASKS_SPEC:
        tid = uuid4()
        task_ids[code] = tid
        session.add(
            MenuTask(
                id=tid,
                code=code,
                display_name=label,
                sort_order=sort_o,
                icon_key=icon_k,
                created_by=admin_id,
                created_ip=SEED_IP,
            )
        )
    await session.flush()

    def add_grants(role_name: str, codes: frozenset[str]) -> None:
        for code in codes:
            if code not in task_ids:
                continue
            session.add(
                RoleTaskGrant(
                    id=uuid4(),
                    role_id=role_ids[role_name],
                    menu_task_id=task_ids[code],
                    can_create=True,
                    can_read=True,
                    can_update=True,
                    can_delete=True,
                    show_in_menu=True,
                    created_by=admin_id,
                    created_ip=SEED_IP,
                )
            )

    # ADMIN: all menu tasks
    add_grants("ADMIN", frozenset(task_ids.keys()))
    # DEV: limited menu
    add_grants("DEV", DEV_MENU_CODES)
    # DELIVERY: orders only (assigned list from API)
    add_grants("DELIVERY", frozenset({"orders"}))

    # --- Masters: categories, brands, medicines, offerings ---
    cat_id = uuid4()
    session.add(
        MedicineCategory(
            id=cat_id,
            name="General",
            description="OTC and general medicines",
            created_by=admin_id,
            created_ip=SEED_IP,
        )
    )
    cat2_id = uuid4()
    session.add(
        MedicineCategory(
            id=cat2_id,
            name="Cardiac",
            description="Heart and BP",
            created_by=admin_id,
            created_ip=SEED_IP,
        )
    )

    brand1 = uuid4()
    brand2 = uuid4()
    session.add(Brand(id=brand1, name="Sun Pharma", description="Sample brand", created_by=admin_id, created_ip=SEED_IP))
    session.add(Brand(id=brand2, name="Cipla", description="Sample brand", created_by=admin_id, created_ip=SEED_IP))
    # Flush parents before medicines so FK inserts are ordered (batch insert can reorder otherwise).
    await session.flush()

    med1 = uuid4()
    med2 = uuid4()
    session.add(
        Medicine(
            id=med1,
            medicine_category_id=cat_id,
            name="Paracetamol 500mg",
            is_prescription_required=False,
            description="Pain relief",
            is_available=True,
            created_by=admin_id,
            created_ip=SEED_IP,
        )
    )
    session.add(
        Medicine(
            id=med2,
            medicine_category_id=cat2_id,
            name="Atorvastatin 10mg",
            is_prescription_required=True,
            description="Cholesterol",
            is_available=True,
            created_by=admin_id,
            created_ip=SEED_IP,
        )
    )
    await session.flush()

    offering1 = uuid4()
    offering2 = uuid4()
    session.add(
        MedicineBrandOffering(
            id=offering1,
            medicine_id=med1,
            brand_id=brand1,
            manufacturer="Sun Pharma Ltd",
            mrp=Decimal("35.00"),
            description="Strip of 10",
            is_available=True,
            created_by=admin_id,
            created_ip=SEED_IP,
        )
    )
    session.add(
        MedicineBrandOffering(
            id=offering2,
            medicine_id=med2,
            brand_id=brand2,
            manufacturer="Cipla Ltd",
            mrp=Decimal("120.00"),
            description="Strip of 10",
            is_available=True,
            created_by=admin_id,
            created_ip=SEED_IP,
        )
    )
    await session.flush()

    session.add(
        Inventory(
            id=uuid4(),
            medicine_brand_offering_id=offering1,
            stock_quantity=500,
            created_by=admin_id,
            created_ip=SEED_IP,
        )
    )
    session.add(
        Inventory(
            id=uuid4(),
            medicine_brand_offering_id=offering2,
            stock_quantity=200,
            created_by=admin_id,
            created_ip=SEED_IP,
        )
    )

    # --- Doctor & polyclinic test ---
    doc_id = uuid4()
    session.add(
        Doctor(
            id=doc_id,
            name="Dr. Sample Physician",
            specialty="General Medicine",
            qualifications="MBBS",
            morning_start=time(9, 0),
            morning_end=time(13, 0),
            evening_start=time(16, 0),
            evening_end=time(20, 0),
            morning_timings="9:00 AM - 1:00 PM",
            evening_timings="4:00 PM - 8:00 PM",
            consultation_fee=Decimal("300.00"),
            created_by=admin_id,
            created_ip=SEED_IP,
        )
    )
    test_id = uuid4()
    session.add(
        PolyclinicTest(
            id=test_id,
            name="Complete Blood Count",
            description="CBC",
            price=Decimal("400.00"),
            duration="Same day",
            fasting_required=False,
            icon_name="Droplet",
            created_by=admin_id,
            created_ip=SEED_IP,
        )
    )

    # --- Coupon & delivery settings ---
    coupon_id = uuid4()
    session.add(
        Coupon(
            id=coupon_id,
            code="WELCOME10",
            discount_percentage=Decimal("10.00"),
            expiry_date=date.today().replace(year=date.today().year + 1),
            min_order_amount=Decimal("100.00"),
            usage_limit=1000,
            usage_count=0,
            first_order_only=False,
            created_by=admin_id,
            created_ip=SEED_IP,
        )
    )

    session.add(
        DeliverySetting(
            id=uuid4(),
            is_enabled=True,
            min_order_amount=Decimal("0.00"),
            delivery_fee=Decimal("40.00"),
            free_delivery_threshold=Decimal("500.00"),
            free_delivery_max_amount=None,
            show_marquee=True,
            created_by=admin_id,
            created_ip=SEED_IP,
        )
    )

    # --- Customer address ---
    cust_uid = user_ids["customer@newbalan.com"]
    addr_id = uuid4()
    session.add(
        Address(
            id=addr_id,
            user_id=cust_uid,
            label="Home",
            street="12 Sample Street",
            city="Chennai",
            state="Tamil Nadu",
            pincode="600001",
            country="India",
            is_default=True,
            created_by=cust_uid,
            created_ip=SEED_IP,
        )
    )
    await session.flush()

    # --- Transactions ---
    appt_id = uuid4()
    session.add(
        Appointment(
            id=appt_id,
            doctor_id=doc_id,
            patient_name="John Patient",
            patient_phone="9876543210",
            appointment_date=date.today(),
            appointment_time=time(10, 0),
            status="CONFIRMED",
            message="Follow-up",
            created_by=cust_uid,
            created_ip=SEED_IP,
        )
    )

    tb_id = uuid4()
    session.add(
        TestBooking(
            id=tb_id,
            test_id=test_id,
            patient_name="Jane Patient",
            patient_phone="9876543211",
            booking_date=date.today(),
            booking_time="11:00 AM",
            status="PENDING",
            created_by=cust_uid,
            created_ip=SEED_IP,
        )
    )

    order1_id = uuid4()
    session.add(
        Order(
            id=order1_id,
            order_reference="SEED_ORDER_001",
            customer_id=cust_uid,
            customer_name="Customer User",
            customer_phone="9999999997",
            customer_email="customer@newbalan.com",
            delivery_address="12 Sample Street, Chennai, Tamil Nadu - 600001, India",
            pincode="600001",
            city="Chennai",
            order_status="DELIVERED",
            total_amount=Decimal("190.00"),
            discount_amount=Decimal("19.00"),
            delivery_fee=Decimal("0.00"),
            final_amount=Decimal("171.00"),
            payment_method="RAZORPAY",
            payment_completed_at=datetime.now(timezone.utc),
            notes="Seed order",
            created_by=cust_uid,
            created_ip=SEED_IP,
        )
    )

    session.add(
        OrderItem(
            id=uuid4(),
            order_id=order1_id,
            medicine_brand_id=offering1,
            medicine_name="Paracetamol 500mg",
            brand_name="Sun Pharma",
            quantity=2,
            unit_price=Decimal("35.00"),
            total_price=Decimal("70.00"),
            requires_prescription=False,
            created_by=cust_uid,
            created_ip=SEED_IP,
        )
    )
    session.add(
        OrderItem(
            id=uuid4(),
            order_id=order1_id,
            medicine_brand_id=offering2,
            medicine_name="Atorvastatin 10mg",
            brand_name="Cipla",
            quantity=1,
            unit_price=Decimal("120.00"),
            total_price=Decimal("120.00"),
            requires_prescription=True,
            created_by=cust_uid,
            created_ip=SEED_IP,
        )
    )

    session.add(
        Payment(
            id=uuid4(),
            order_id=order1_id,
            payment_method="RAZORPAY",
            payment_status="SUCCESS",
            amount=Decimal("171.00"),
            merchant_transaction_id="seed_txn_001",
            gateway_transaction_id="seed_pay_001",
            payment_date=datetime.now(timezone.utc),
            refund_status="NONE",
            refund_amount=Decimal("0"),
            created_by=cust_uid,
            created_ip=SEED_IP,
        )
    )
    await session.flush()

    session.add(
        CouponUsage(
            id=uuid4(),
            coupon_id=coupon_id,
            order_id=order1_id,
            customer_id=cust_uid,
            discount_amount=Decimal("19.00"),
            coupon_code="WELCOME10",
            customer_name="Customer User",
            customer_phone="9999999997",
            order_final_amount=Decimal("171.00"),
            created_by=cust_uid,
            created_ip=SEED_IP,
        )
    )

    await session.flush()


async def main_async() -> None:
    parser = argparse.ArgumentParser(description="Seed RBAC, users, and sample data.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Truncate all application tables (destructive) before seeding.",
    )
    parser.add_argument(
        "--password",
        default=DEFAULT_PASSWORD,
        help=f"Password for admin/dev/customer users (default: {DEFAULT_PASSWORD})",
    )
    args = parser.parse_args()

    DatabaseConnection.initialize()
    await DatabaseConnection.create_tables()

    factory = DatabaseConnection.get_session_factory()
    async with factory() as session:
        if args.reset:
            await _truncate_all(session)
            await session.commit()
            print("[OK] Tables truncated.")

        existing = await session.scalar(select(func.count()).select_from(Role))
        if existing and existing > 0 and not args.reset:
            print("[INFO] Roles already present. Use --reset to re-seed.")
            return

        await seed(session, args.password)
        await session.commit()

    print("[OK] Seed completed.")
    print("    Users (same password):")
    for email, name, role, _ in USERS_SPEC:
        print(f"      {email}  ({role})  — {name}")


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
