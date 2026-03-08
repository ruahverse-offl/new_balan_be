"""
SQLAlchemy Database Models
Base models and table definitions
"""

from sqlalchemy import Column, String, Boolean, Text, Integer, Date, Numeric, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import text
from sqlalchemy.orm import relationship
from datetime import timezone, timedelta
from app.db.db_connection import Base

# IST timezone (UTC+5:30)
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


# Master Tables
class Role(MasterModel):
    """Roles table model."""
    
    __tablename__ = "roles"
    
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)


class Permission(MasterModel):
    """Permissions table model."""
    
    __tablename__ = "permissions"
    
    code = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)


class RolePermission(MasterModel):
    """Role Permissions table model."""
    
    __tablename__ = "role_permissions"
    
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id"), nullable=False)


class User(MasterModel):
    """Users table model."""
    
    __tablename__ = "users"
    
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    full_name = Column(String(255), nullable=False)
    mobile_number = Column(String(15), nullable=False)
    email = Column(String(255), nullable=False)
    password_hash = Column(Text, nullable=False)


class PharmacistProfile(MasterModel):
    """Pharmacist Profiles table model."""
    
    __tablename__ = "pharmacist_profiles"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    license_number = Column(String(100), nullable=False)
    license_valid_till = Column(Date, nullable=False)


class TherapeuticCategory(MasterModel):
    """Therapeutic Categories table model."""
    
    __tablename__ = "therapeutic_categories"
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)


class Medicine(MasterModel):
    """Medicines table model."""
    
    __tablename__ = "medicines"
    
    name = Column(String(255), nullable=False)
    dosage_form = Column(String(100), nullable=False)
    therapeutic_category_id = Column(UUID(as_uuid=True), ForeignKey("therapeutic_categories.id"), nullable=False)
    is_prescription_required = Column(Boolean, nullable=False, default=False)
    is_controlled = Column(Boolean, nullable=False, default=False)
    schedule_type = Column(String(10), nullable=False)
    description = Column(Text, nullable=True)


class MedicineComposition(MasterModel):
    """Medicine Compositions table model."""
    
    __tablename__ = "medicine_compositions"
    
    medicine_id = Column(UUID(as_uuid=True), ForeignKey("medicines.id"), nullable=False)
    salt_name = Column(String(255), nullable=False)
    strength = Column(String(50), nullable=False)
    unit = Column(String(20), nullable=False)


class MedicineBrand(MasterModel):
    """Medicine Brands table model."""
    
    __tablename__ = "medicine_brands"
    
    medicine_id = Column(UUID(as_uuid=True), ForeignKey("medicines.id"), nullable=False)
    brand_name = Column(String(255), nullable=False)
    manufacturer = Column(String(255), nullable=False)
    mrp = Column(Numeric(10, 2), nullable=False)
    description = Column(Text, nullable=True)


# Transaction Tables
class ProductBatch(BaseModel):
    """Product Batches table model."""
    
    __tablename__ = "product_batches"
    
    medicine_brand_id = Column(UUID(as_uuid=True), ForeignKey("medicine_brands.id"), nullable=False)
    batch_number = Column(String(100), nullable=False)
    expiry_date = Column(Date, nullable=False)
    purchase_price = Column(Numeric(10, 2), nullable=False)
    quantity_available = Column(Integer, nullable=False)


class InventoryTransaction(BaseModel):
    """Inventory Transactions table model."""
    
    __tablename__ = "inventory_transactions"
    
    medicine_brand_id = Column(UUID(as_uuid=True), ForeignKey("medicine_brands.id"), nullable=False)
    product_batch_id = Column(UUID(as_uuid=True), ForeignKey("product_batches.id"), nullable=False)
    transaction_type = Column(String(50), nullable=False)
    quantity_change = Column(Integer, nullable=False)
    reference_order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    remarks = Column(Text, nullable=True)


class Order(BaseModel):
    """Orders table model.
    id = UUID (primary key, for DB and APIs).
    order_reference = human-readable order id: date_time_username (e.g. 20250308_073015_john_doe).
    """
    
    __tablename__ = "orders"
    
    order_reference = Column(String(100), unique=True, nullable=True, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    customer_name = Column(String(255), nullable=True)
    customer_phone = Column(String(15), nullable=False)
    customer_email = Column(String(255), nullable=True)
    delivery_address = Column(Text, nullable=False)
    pincode = Column(String(10), nullable=True)
    city = Column(String(100), nullable=True)
    order_source = Column(String(50), nullable=False)
    order_status = Column(String(50), nullable=False)
    approval_status = Column(String(50), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    discount_amount = Column(Numeric(10, 2), nullable=False, default=0)
    delivery_fee = Column(Numeric(10, 2), nullable=False, default=0)
    final_amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String(50), nullable=False)
    payment_completed_at = Column(DateTime(timezone=True), nullable=True)
    prescription_id = Column(String(100), nullable=True)
    processed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)


class Payment(BaseModel):
    """Payments table model — tracks every payment transaction end-to-end."""

    __tablename__ = "payments"

    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    payment_method = Column(String(50), nullable=False)
    payment_status = Column(String(50), nullable=False)  # INITIATED / PENDING / SUCCESS / FAILED
    amount = Column(Numeric(10, 2), nullable=False)

    # Gateway transaction tracking (Razorpay: order_id, payment_id)
    merchant_transaction_id = Column(String(100), nullable=True)   # Our receipt/order ref
    gateway_transaction_id = Column(String(100), nullable=True)   # Razorpay payment_id
    gateway_order_id = Column(String(100), nullable=True)         # Razorpay order_id
    gateway_response = Column(Text, nullable=True)                 # Full JSON response for audit
    payment_date = Column(DateTime(timezone=True), nullable=True)  # When payment completed

    # Refund tracking
    refund_status = Column(String(50), nullable=False, default="NONE")  # NONE / INITIATED / COMPLETED / FAILED
    refund_amount = Column(Numeric(10, 2), nullable=False, default=0)
    refund_transaction_id = Column(String(100), nullable=True)


# ============================================
# CLINIC & POLYCLINIC MODULE
# ============================================

class Doctor(MasterModel):
    """Doctors table model."""
    
    __tablename__ = "doctors"
    
    name = Column(String(255), nullable=False)
    specialty = Column(String(255), nullable=False)
    qualifications = Column(Text, nullable=True)
    morning_timings = Column(String(100), nullable=True)
    evening_timings = Column(String(100), nullable=True)
    image_url = Column(Text, nullable=True)
    consultation_fee = Column(Numeric(10, 2), nullable=True)


class Appointment(BaseModel):
    """Appointments table model."""
    
    __tablename__ = "appointments"
    
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctors.id"), nullable=True)  # nullable for legacy rows; new rows should set it
    patient_name = Column(String(255), nullable=False)
    patient_phone = Column(String(15), nullable=False)
    appointment_date = Column(Date, nullable=False)
    appointment_time = Column(String(50), nullable=True)
    status = Column(String(50), nullable=False, default="PENDING")
    message = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)


class PolyclinicTest(MasterModel):
    """Polyclinic Tests table model."""
    
    __tablename__ = "polyclinic_tests"
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    duration = Column(String(50), nullable=True)
    fasting_required = Column(Boolean, nullable=False, default=False)
    icon_name = Column(String(100), nullable=True)


class TestBooking(BaseModel):
    """Test Bookings table model."""
    
    __tablename__ = "test_bookings"
    
    test_id = Column(UUID(as_uuid=True), ForeignKey("polyclinic_tests.id"), nullable=False)
    patient_name = Column(String(255), nullable=False)
    patient_phone = Column(String(15), nullable=False)
    booking_date = Column(Date, nullable=False)
    booking_time = Column(String(50), nullable=True)
    status = Column(String(50), nullable=False, default="PENDING")
    notes = Column(Text, nullable=True)


class InsuranceEnquiry(BaseModel):
    """Insurance Enquiries table model."""

    __tablename__ = "insurance_enquiries"

    customer_name = Column(String(255), nullable=False)
    customer_phone = Column(String(15), nullable=False)
    customer_age = Column(Integer, nullable=True)
    family_size = Column(Integer, nullable=True)
    plan_type = Column(String(100), nullable=True)
    message = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="PENDING")
    admin_notes = Column(Text, nullable=True)


# ============================================
# PHARMACY MODULE - ADDITIONAL
# ============================================

class ProductCategory(MasterModel):
    """Product Categories table model."""
    
    __tablename__ = "product_categories"
    
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)


class Coupon(MasterModel):
    """Coupons table model."""
    
    __tablename__ = "coupons"
    
    code = Column(String(50), nullable=False, unique=True)
    discount_percentage = Column(Numeric(5, 2), nullable=False)
    expiry_date = Column(Date, nullable=True)
    min_order_amount = Column(Numeric(10, 2), nullable=True)
    max_discount_amount = Column(Numeric(10, 2), nullable=True)
    usage_limit = Column(Integer, nullable=True)
    usage_count = Column(Integer, nullable=False, default=0)
    first_order_only = Column(Boolean, nullable=False, default=False, server_default=text("false"))


class CouponUsage(BaseModel):
    """Coupon Usages table model.
    Stores a snapshot of coupon usage at order time: coupon code, customer, phone, order total.
    These snapshot columns ensure we can display full usage details even if coupon/order is later deleted.
    """
    
    __tablename__ = "coupon_usages"
    
    coupon_id = Column(UUID(as_uuid=True), ForeignKey("coupons.id"), nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    discount_amount = Column(Numeric(10, 2), nullable=False)
    # Snapshot fields — stored at order time so Coupon Usages page always has full data
    coupon_code = Column(String(50), nullable=True)
    customer_name = Column(String(255), nullable=True)
    customer_phone = Column(String(15), nullable=True)
    order_final_amount = Column(Numeric(10, 2), nullable=True)


class DeliverySetting(MasterModel):
    """Delivery Settings table model (Singleton)."""
    
    __tablename__ = "delivery_settings"
    
    is_enabled = Column(Boolean, nullable=False, default=True)
    min_order_amount = Column(Numeric(10, 2), nullable=False)
    delivery_fee = Column(Numeric(10, 2), nullable=False)
    free_delivery_threshold = Column(Numeric(10, 2), nullable=False)
    delivery_zones = Column(Text, nullable=True)  # JSON stored as TEXT (PostgreSQL JSONB not available in all versions)
    show_marquee = Column(Boolean, nullable=False, default=True)


class DeliverySlot(MasterModel):
    """Delivery Slots table model."""
    
    __tablename__ = "delivery_slots"
    
    delivery_settings_id = Column(UUID(as_uuid=True), ForeignKey("delivery_settings.id"), nullable=False)
    slot_time = Column(String(100), nullable=False)
    slot_order = Column(Integer, nullable=False)


# ============================================
# ORDERS ENHANCEMENT
# ============================================

class OrderItem(BaseModel):
    """Order Items table model."""
    
    __tablename__ = "order_items"
    
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    medicine_brand_id = Column(UUID(as_uuid=True), ForeignKey("medicine_brands.id"), nullable=False)
    medicine_name = Column(String(255), nullable=True)
    brand_name = Column(String(255), nullable=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    requires_prescription = Column(Boolean, nullable=False, default=False)
    product_batch_id = Column(UUID(as_uuid=True), ForeignKey("product_batches.id"), nullable=True)


# ============================================
# PRESCRIPTIONS MODULE
# ============================================

class Prescription(BaseModel):
    """Prescriptions table model."""

    __tablename__ = "prescriptions"

    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    file_url = Column(Text, nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="PENDING")
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    review_notes = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)


class Address(MasterModel):
    """User Addresses table model."""

    __tablename__ = "addresses"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    label = Column(String(50), nullable=True)
    street = Column(Text, nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    pincode = Column(String(10), nullable=False)
    country = Column(String(100), nullable=False, default="India")
    is_default = Column(Boolean, nullable=False, default=False, server_default=text("false"))