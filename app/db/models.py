"""
SQLAlchemy Database Models
Base models and table definitions.

Naming: master tables use prefix ``M_``, transaction tables use prefix ``T_``.
"""

from sqlalchemy import Column, String, Boolean, Text, Integer, Date, Time, Numeric, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import text
from datetime import timezone, timedelta
from app.db.db_connection import Base

IST = timezone(timedelta(hours=5, minutes=30))


class BaseModel(Base):
    """Base model with audit fields for all tables."""

    __abstract__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    created_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("timezone('Asia/Kolkata', now())"))
    created_ip = Column(String(45), nullable=False)
    updated_by = Column(UUID(as_uuid=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True, server_default=text("timezone('Asia/Kolkata', now())"), onupdate=text("timezone('Asia/Kolkata', now())"))
    updated_ip = Column(String(45), nullable=True)
    is_deleted = Column(Boolean, nullable=False, default=False, server_default=text("false"))


class MasterModel(BaseModel):
    """Base model for master tables with is_active field."""

    __abstract__ = True

    is_active = Column(Boolean, nullable=False, default=True, server_default=text("true"))


class Role(MasterModel):
    __tablename__ = "M_roles"
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)


class Permission(MasterModel):
    __tablename__ = "M_permissions"
    code = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)


class RolePermission(MasterModel):
    __tablename__ = "M_role_permissions"
    role_id = Column(UUID(as_uuid=True), ForeignKey("M_roles.id"), nullable=False)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("M_permissions.id"), nullable=False)


class MenuTask(MasterModel):
    """
    Admin UI task (screen) — one row per sidebar destination.

    ``code`` matches the frontend admin tab id (e.g. medicines, therapeutic-categories).
    """

    __tablename__ = "M_menu_tasks"

    code = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(255), nullable=False)
    sort_order = Column(Integer, nullable=False, server_default=text("0"))
    icon_key = Column(String(100), nullable=True)


class RoleTaskGrant(BaseModel):
    """
    Per-role grants for a menu task: CRUD flags and whether the task appears in the sidebar.

    Sidebar entries are returned only when ``show_in_menu`` and ``can_read`` are true.
    """

    __tablename__ = "M_role_task_grants"

    role_id = Column(UUID(as_uuid=True), ForeignKey("M_roles.id"), nullable=False)
    menu_task_id = Column(UUID(as_uuid=True), ForeignKey("M_menu_tasks.id"), nullable=False)
    can_create = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    can_read = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    can_update = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    can_delete = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    show_in_menu = Column(Boolean, nullable=False, default=False, server_default=text("false"))

    __table_args__ = (
        UniqueConstraint("role_id", "menu_task_id", name="uq_m_role_task_grants_role_task"),
    )


class User(MasterModel):
    __tablename__ = "M_users"
    role_id = Column(UUID(as_uuid=True), ForeignKey("M_roles.id"), nullable=False)
    full_name = Column(String(255), nullable=False)
    mobile_number = Column(String(15), nullable=False)
    email = Column(String(255), nullable=False)
    password_hash = Column(Text, nullable=False)


class MedicineCategory(MasterModel):
    """Medicine category (formerly therapeutic category)."""

    __tablename__ = "M_medicine_categories"

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)


class Brand(MasterModel):
    """Shared master brand (e.g. trade name / line)."""

    __tablename__ = "M_brands"

    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)


class Medicine(MasterModel):
    """Medicine catalog row — clinical/parent entity."""

    __tablename__ = "M_medicines"

    medicine_category_id = Column(UUID(as_uuid=True), ForeignKey("M_medicine_categories.id"), nullable=False)
    name = Column(String(255), nullable=False)
    is_prescription_required = Column(Boolean, nullable=False, default=False)
    description = Column(Text, nullable=True)
    is_available = Column(Boolean, nullable=False, default=True, server_default=text("true"))
    # Relative path under LOCAL_STORAGE_PATH (default …/storage/devstorage), e.g. medicine/uuid.png → served at /storage/medicine/...
    image_path = Column(String(512), nullable=True)


class MedicineBrandOffering(MasterModel):
    """Junction: one medicine + one shared brand, with commercial fields (MRP, manufacturer, etc.)."""

    __tablename__ = "M_medicine_brand_offerings"

    __table_args__ = (UniqueConstraint("medicine_id", "brand_id", name="uq_m_medicine_brand_offerings_pair"),)

    medicine_id = Column(UUID(as_uuid=True), ForeignKey("M_medicines.id"), nullable=False)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("M_brands.id"), nullable=False)
    manufacturer = Column(String(255), nullable=False)
    mrp = Column(Numeric(10, 2), nullable=False)
    description = Column(Text, nullable=True)
    is_available = Column(Boolean, nullable=False, default=True, server_default=text("true"))


class Order(BaseModel):
    __tablename__ = "T_orders"

    order_reference = Column(String(100), unique=True, nullable=True, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("M_users.id"), nullable=True)
    customer_name = Column(String(255), nullable=True)
    customer_phone = Column(String(15), nullable=False)
    customer_email = Column(String(255), nullable=True)
    delivery_address = Column(Text, nullable=False)
    pincode = Column(String(10), nullable=True)
    city = Column(String(100), nullable=True)
    order_status = Column(String(50), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    discount_amount = Column(Numeric(10, 2), nullable=False, default=0)
    delivery_fee = Column(Numeric(10, 2), nullable=False, default=0)
    final_amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String(50), nullable=False)
    payment_completed_at = Column(DateTime(timezone=True), nullable=True)
    processed_by = Column(UUID(as_uuid=True), ForeignKey("M_users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    prescription_path = Column(Text, nullable=True)
    delivery_assigned_user_id = Column(UUID(as_uuid=True), ForeignKey("M_users.id"), nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    cancelled_by_user_id = Column(UUID(as_uuid=True), ForeignKey("M_users.id"), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    return_reason = Column(Text, nullable=True)


class Payment(BaseModel):
    __tablename__ = "T_payments"

    order_id = Column(UUID(as_uuid=True), ForeignKey("T_orders.id"), nullable=False)
    payment_method = Column(String(50), nullable=False)
    payment_status = Column(String(50), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    merchant_transaction_id = Column(String(100), nullable=True)
    gateway_transaction_id = Column(String(100), nullable=True)
    gateway_order_id = Column(String(100), nullable=True)
    gateway_response = Column(Text, nullable=True)
    payment_date = Column(DateTime(timezone=True), nullable=True)
    refund_status = Column(String(50), nullable=False, default="NONE")
    refund_amount = Column(Numeric(10, 2), nullable=False, default=0)
    refund_transaction_id = Column(String(100), nullable=True)


class Doctor(MasterModel):
    __tablename__ = "M_doctors"
    name = Column(String(255), nullable=False)
    specialty = Column(String(255), nullable=False)
    qualifications = Column(Text, nullable=True)
    sub_specialty = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    experience = Column(Text, nullable=True)
    education = Column(Text, nullable=True)
    specializations = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    morning_start = Column(Time, nullable=True)
    morning_end = Column(Time, nullable=True)
    evening_start = Column(Time, nullable=True)
    evening_end = Column(Time, nullable=True)
    morning_timings = Column(String(100), nullable=True)
    evening_timings = Column(String(100), nullable=True)
    image_url = Column(Text, nullable=True)
    consultation_fee = Column(Numeric(10, 2), nullable=True)


class Appointment(BaseModel):
    __tablename__ = "T_appointments"
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("M_doctors.id"), nullable=True)
    patient_name = Column(String(255), nullable=False)
    patient_phone = Column(String(15), nullable=False)
    appointment_date = Column(Date, nullable=False)
    appointment_time = Column(Time, nullable=True)
    status = Column(String(50), nullable=False, default="PENDING")
    message = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)


class PolyclinicTest(MasterModel):
    __tablename__ = "M_polyclinic_tests"
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    duration = Column(String(50), nullable=True)
    fasting_required = Column(Boolean, nullable=False, default=False)
    icon_name = Column(String(100), nullable=True)


class TestBooking(BaseModel):
    __tablename__ = "T_test_bookings"
    test_id = Column(UUID(as_uuid=True), ForeignKey("M_polyclinic_tests.id"), nullable=False)
    patient_name = Column(String(255), nullable=False)
    patient_phone = Column(String(15), nullable=False)
    booking_date = Column(Date, nullable=False)
    booking_time = Column(String(50), nullable=True)
    status = Column(String(50), nullable=False, default="PENDING")
    notes = Column(Text, nullable=True)


class Coupon(MasterModel):
    __tablename__ = "M_coupons"
    code = Column(String(50), nullable=False, unique=True)
    discount_percentage = Column(Numeric(5, 2), nullable=False)
    expiry_date = Column(Date, nullable=True)
    min_order_amount = Column(Numeric(10, 2), nullable=True)
    max_discount_amount = Column(Numeric(10, 2), nullable=True)
    usage_limit = Column(Integer, nullable=True)
    usage_count = Column(Integer, nullable=False, default=0)
    first_order_only = Column(Boolean, nullable=False, default=False, server_default=text("false"))


class CouponUsage(BaseModel):
    __tablename__ = "T_coupon_usages"
    coupon_id = Column(UUID(as_uuid=True), ForeignKey("M_coupons.id"), nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey("T_orders.id"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("M_users.id"), nullable=True)
    discount_amount = Column(Numeric(10, 2), nullable=False)
    coupon_code = Column(String(50), nullable=True)
    customer_name = Column(String(255), nullable=True)
    customer_phone = Column(String(15), nullable=True)
    order_final_amount = Column(Numeric(10, 2), nullable=True)


class DeliverySetting(MasterModel):
    __tablename__ = "M_delivery_settings"
    is_enabled = Column(Boolean, nullable=False, default=True)
    min_order_amount = Column(Numeric(10, 2), nullable=False)
    delivery_fee = Column(Numeric(10, 2), nullable=False)
    free_delivery_threshold = Column(Numeric(10, 2), nullable=False)
    free_delivery_max_amount = Column(Numeric(10, 2), nullable=True)
    delivery_zones = Column(Text, nullable=True)
    show_marquee = Column(Boolean, nullable=False, default=True)
    delivery_slot_times = Column(Text, nullable=True)


class OrderItem(BaseModel):
    __tablename__ = "T_order_items"
    order_id = Column(UUID(as_uuid=True), ForeignKey("T_orders.id"), nullable=False)
    medicine_brand_id = Column(UUID(as_uuid=True), ForeignKey("M_medicine_brand_offerings.id"), nullable=False)
    medicine_name = Column(String(255), nullable=True)
    brand_name = Column(String(255), nullable=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    requires_prescription = Column(Boolean, nullable=False, default=False)


class Address(MasterModel):
    __tablename__ = "M_addresses"
    user_id = Column(UUID(as_uuid=True), ForeignKey("M_users.id"), nullable=False)
    label = Column(String(50), nullable=True)
    street = Column(Text, nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    pincode = Column(String(10), nullable=False)
    country = Column(String(100), nullable=False, default="India")
    is_default = Column(Boolean, nullable=False, default=False, server_default=text("false"))


class Inventory(MasterModel):
    """On-hand units per medicine–brand offering (SKU)."""

    __tablename__ = "M_inventory"

    __table_args__ = (
        UniqueConstraint("medicine_brand_offering_id", name="uq_m_inventory_offering"),
    )

    medicine_brand_offering_id = Column(
        UUID(as_uuid=True), ForeignKey("M_medicine_brand_offerings.id"), nullable=False, index=True
    )
    stock_quantity = Column(Integer, nullable=False, server_default=text("0"))


class InventoryAlert(BaseModel):
    """
    Active low-stock signal for an offering.

    Rows are removed when stock is refilled to at or above ``INV_STOCK_THRESHOLD``.
    """

    __tablename__ = "T_inventory_alerts"

    __table_args__ = (
        UniqueConstraint("medicine_brand_offering_id", name="uq_t_inventory_alerts_offering"),
    )

    medicine_brand_offering_id = Column(
        UUID(as_uuid=True), ForeignKey("M_medicine_brand_offerings.id"), nullable=False, index=True
    )
    current_stock = Column(Integer, nullable=False)
