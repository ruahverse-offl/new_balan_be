"""
Database migrations (add missing columns, etc.).
SQLAlchemy create_all() does not add columns to existing tables.
Run these after create_tables() on startup.
"""

import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)


async def run_migrations(engine):
    """
    Run migrations to add any missing columns to existing tables.
    """
    async with engine.begin() as conn:
        await _ensure_appointments_doctor_id(conn)
        await _ensure_coupon_usages_snapshot_columns(conn)
        await _ensure_coupons_first_order_only(conn)
        await _ensure_orders_extra_columns(conn)
        await _ensure_orders_order_reference(conn)
        await _ensure_order_items_snapshot_columns(conn)
        await _ensure_therapeutic_categories_seed(conn)


async def _ensure_appointments_doctor_id(conn):
    """Add doctor_id to appointments if the table exists but the column does not."""
    # Check if appointments table exists
    table_result = await conn.execute(
        text("""
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'appointments'
        """)
    )
    if table_result.scalar() is None:
        logger.info("appointments table does not exist yet (create_tables will create it with doctor_id)")
        return
    # Check if column already exists
    col_result = await conn.execute(
        text("""
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'appointments' AND column_name = 'doctor_id'
        """)
    )
    if col_result.scalar() is not None:
        logger.info("appointments.doctor_id column already exists")
        return
    logger.info("Adding doctor_id column to appointments table...")
    await conn.execute(
        text("""
            ALTER TABLE appointments
            ADD COLUMN doctor_id UUID REFERENCES doctors(id)
        """)
    )
    logger.info("appointments.doctor_id column added successfully")


async def _ensure_coupon_usages_snapshot_columns(conn):
    """Add snapshot columns to coupon_usages (coupon_code, customer_name, customer_phone, order_final_amount)."""
    table_result = await conn.execute(
        text("""
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'coupon_usages'
        """)
    )
    if table_result.scalar() is None:
        return
    for col in ["coupon_code", "customer_name", "customer_phone", "order_final_amount"]:
        col_result = await conn.execute(
            text("""
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'coupon_usages' AND column_name = :col
            """),
            {"col": col},
        )
        if col_result.scalar() is not None:
            continue
        type_sql = "VARCHAR(50)" if col == "coupon_code" else "VARCHAR(255)" if col == "customer_name" else "VARCHAR(15)" if col == "customer_phone" else "NUMERIC(10, 2)"
        await conn.execute(text(f"ALTER TABLE coupon_usages ADD COLUMN {col} {type_sql}"))
        logger.info("coupon_usages.%s column added", col)


async def _ensure_coupons_first_order_only(conn):
    """Add first_order_only to coupons (for first-order-only coupon type)."""
    table_result = await conn.execute(
        text("""
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'coupons'
        """)
    )
    if table_result.scalar() is None:
        return
    col_result = await conn.execute(
        text("""
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'coupons' AND column_name = 'first_order_only'
        """)
    )
    if col_result.scalar() is not None:
        logger.info("coupons.first_order_only column already exists")
        return
    logger.info("Adding first_order_only column to coupons table...")
    await conn.execute(
        text("ALTER TABLE coupons ADD COLUMN first_order_only BOOLEAN NOT NULL DEFAULT false")
    )
    logger.info("coupons.first_order_only column added successfully")


async def _ensure_orders_extra_columns(conn):
    """Add customer_email, pincode, city, payment_completed_at to orders."""
    table_result = await conn.execute(
        text("""
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'orders'
        """)
    )
    if table_result.scalar() is None:
        return
    cols = [
        ("customer_email", "VARCHAR(255)"),
        ("pincode", "VARCHAR(10)"),
        ("city", "VARCHAR(100)"),
        ("payment_completed_at", "TIMESTAMP WITH TIME ZONE"),
    ]
    for col_name, col_type in cols:
        col_result = await conn.execute(
            text("""
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'orders' AND column_name = :col
            """),
            {"col": col_name},
        )
        if col_result.scalar() is not None:
            continue
        await conn.execute(text(f"ALTER TABLE orders ADD COLUMN {col_name} {col_type}"))
        logger.info("orders.%s column added", col_name)


async def _ensure_orders_order_reference(conn):
    """Add order_reference (date_time_username) to orders. id stays UUID."""
    table_result = await conn.execute(
        text("""
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'orders'
        """)
    )
    if table_result.scalar() is None:
        return
    col_result = await conn.execute(
        text("""
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'orders' AND column_name = 'order_reference'
        """)
    )
    if col_result.scalar() is not None:
        logger.info("orders.order_reference column already exists")
        return
    logger.info("Adding order_reference column to orders table...")
    await conn.execute(
        text("ALTER TABLE orders ADD COLUMN order_reference VARCHAR(100) UNIQUE")
    )
    logger.info("orders.order_reference column added successfully")


async def _ensure_order_items_snapshot_columns(conn):
    """Add medicine_name, brand_name, product_batch_id to order_items."""
    table_result = await conn.execute(
        text("""
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'order_items'
        """)
    )
    if table_result.scalar() is None:
        return
    cols = [
        ("medicine_name", "VARCHAR(255)"),
        ("brand_name", "VARCHAR(255)"),
        ("product_batch_id", "UUID REFERENCES product_batches(id)"),
    ]
    for col_name, col_type in cols:
        col_result = await conn.execute(
            text("""
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'order_items' AND column_name = :col
            """),
            {"col": col_name},
        )
        if col_result.scalar() is not None:
            continue
        await conn.execute(text(f"ALTER TABLE order_items ADD COLUMN {col_name} {col_type}"))
        logger.info("order_items.%s column added", col_name)


async def _ensure_therapeutic_categories_seed(conn):
    """Seed default therapeutic categories if the table is empty (so Manage Medicines has a dropdown)."""
    table_result = await conn.execute(
        text("""
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'therapeutic_categories'
        """)
    )
    if table_result.scalar() is None:
        return
    count_result = await conn.execute(
        text("SELECT COUNT(*) FROM therapeutic_categories WHERE is_deleted = false")
    )
    tc_count = count_result.scalar() or 0
    if tc_count > 0:
        logger.info("therapeutic_categories already has data, skipping seed")
        return
    user_result = await conn.execute(text("SELECT id FROM users WHERE is_deleted = false LIMIT 1"))
    user_row = user_result.fetchone()
    if not user_row:
        logger.warning("No user found; cannot seed therapeutic_categories (add categories manually in Therapeutic Cat. tab)")
        return
    created_by = str(user_row[0])
    defaults = [
        ("Analgesics & Antipyretics", "Pain relievers and fever reducers"),
        ("Antibiotics", "Anti-bacterial medicines"),
        ("Antidiabetics", "Medicines for diabetes management"),
        ("Cardiovascular", "Heart and blood pressure medicines"),
        ("Gastrointestinal", "Stomach and digestive medicines"),
        ("Vitamins & Supplements", "Nutritional supplements"),
        ("Antihistamines", "Allergy relief medicines"),
        ("Respiratory", "Medicines for cough and respiratory issues"),
    ]
    for name, description in defaults:
        await conn.execute(
            text("""
                INSERT INTO therapeutic_categories (name, description, is_active, is_deleted, created_by, created_ip)
                VALUES (:name, :desc, true, false, :created_by::uuid, '127.0.0.1')
            """),
            {"name": name, "desc": description or "", "created_by": created_by},
        )
    logger.info("therapeutic_categories seeded with %s default categories", len(defaults))
