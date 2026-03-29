"""
Razorpay Payment Router
Handles payment initiation, verification, status check, and refunds.
"""

import json
import logging
from typing import List, Literal, Optional
from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime, timezone, timedelta
import re
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.db.models import (
    Order,
    OrderItem,
    Payment,
    Coupon,
    CouponUsage,
    MedicineBrandOffering,
    Brand,
    Medicine,
    User,
)
from app.utils.auth import get_current_user_id
from app.utils.rbac import require_permission
from app.utils.request_utils import get_client_ip
from app.config import get_settings
from app.services.razorpay_service import (
    create_order as razorpay_create_order,
    verify_payment_signature,
    fetch_payment,
    process_refund,
)
from app.services import inventory_service
from app.db.models import DeliverySetting
from app.utils.delivery_pricing import delivery_fee_for_subtotal
from app.utils.delivery_windows import (
    fulfillment_meta_to_order_note_line,
    next_delivery_fulfillment_meta,
    slot_labels_from_parsed_items,
)

logger = logging.getLogger(__name__)

# IST for order_reference date/time
IST = timezone(timedelta(hours=5, minutes=30))


def _slug_username(full_name: str) -> str:
    """Convert full_name to username slug: lowercase, spaces to underscores, alphanumeric + underscore only."""
    if not full_name or not full_name.strip():
        return "user"
    s = re.sub(r"[^a-zA-Z0-9\s]", "", full_name.strip())
    s = re.sub(r"\s+", "_", s).lower()
    return s[:50] if s else "user"


def _make_order_reference(username_slug: str) -> str:
    """Format: YYYYMMDD_HHMMSS_username_suffix (suffix = 4 hex for uniqueness)."""
    now = datetime.now(IST)
    date_part = now.strftime("%Y%m%d")
    time_part = now.strftime("%H%M%S")
    suffix = uuid4().hex[:4]
    return f"{date_part}_{time_part}_{username_slug}_{suffix}"


settings = get_settings()

router = APIRouter(prefix="/api/v1/razorpay", tags=["razorpay-payments"])


def _should_expose_exception_details(request: Request) -> bool:
    """
    Expose exception details only for local callers (to avoid leaking internals).
    """
    try:
        if getattr(settings, "DEBUG", False):
            return True
        # Non-production environments are safe for debugging.
        if not settings.is_production():
            return True

        # Local dev: browser typically hits localhost.
        origin = (request.headers.get("origin") or request.headers.get("referer") or "").lower()
        if (
            "localhost" in origin
            or "127.0.0.1" in origin
            or ":5173" in origin
            or "5173" in origin
        ):
            return True

        client_host = (request.client.host or "").lower() if request.client else ""
        if client_host in ("127.0.0.1", "::1"):
            return True
    except Exception:
        return False
    return False


async def _resolve_offering_for_order_item(
    db: AsyncSession, offering_uuid: UUID
):
    """
    Load medicine_brand_offering (cart id) with medicine name, brand display name, and Rx flag.
    Returns (medicine_name, brand_display_name, requires_prescription) or (None, None, None) if not found.
    """
    stmt = (
        select(Medicine.name, Brand.name, Medicine.is_prescription_required)
        .select_from(MedicineBrandOffering)
        .join(Medicine, MedicineBrandOffering.medicine_id == Medicine.id)
        .join(Brand, MedicineBrandOffering.brand_id == Brand.id)
        .where(
            MedicineBrandOffering.id == offering_uuid,
            MedicineBrandOffering.is_deleted == False,  # noqa: E712
        )
    )
    row = (await db.execute(stmt)).first()
    if not row:
        return None, None, None
    return row[0], row[1], bool(row[2])


def _validated_prescription_path(raw: Optional[str], required: bool) -> Optional[str]:
    """
    Normalize and validate prescription reference from upload API (stored_as or url).
    Returns None if optional and empty; raises HTTPException if invalid or missing when required.
    """
    p = (raw or "").strip()
    if not p:
        if required:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A prescription upload is required for one or more medicines in your cart.",
            )
        return None
    if ".." in p or "\n" in p or "\r" in p:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid prescription reference.",
        )
    if p.startswith("prescription/") and len(p) > len("prescription/"):
        return p
    if p.startswith("/storage/prescription/") and len(p) > len("/storage/prescription/"):
        return p
    if p.startswith("https://") or p.startswith("http://"):
        return p
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid prescription reference. Please upload your prescription again.",
    )


# ─── Request / Response Schemas ───


class CartItemSchema(BaseModel):
    medicine_brand_id: Optional[str] = None
    name: str
    quantity: int = Field(ge=1)
    price: float = Field(ge=0)
    requires_prescription: bool = False


def _offering_qty_from_cart_items(items: List[CartItemSchema]) -> List[tuple[UUID, int]]:
    """Parse medicine_brand_offering UUID and quantity from each cart line."""
    out: List[tuple[UUID, int]] = []
    for item in items:
        brand_id = item.medicine_brand_id
        if brand_id and "_" in brand_id:
            brand_id = brand_id.split("_")[-1]
        if not brand_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing medicine_brand_id for item: {item.name}",
            )
        try:
            brand_uuid = UUID(brand_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid medicine_brand_id for item: {item.name}",
            )
        out.append((brand_uuid, item.quantity))
    return out


async def _cart_requires_prescription_from_catalog(
    db: AsyncSession, items: List[CartItemSchema]
) -> bool:
    """True if any cart line's medicine is prescription-required (from DB, not client flags)."""
    oq = _offering_qty_from_cart_items(items)
    offering_ids = [uid for uid, _ in oq]
    if not offering_ids:
        return False
    stmt = (
        select(Medicine.is_prescription_required)
        .select_from(MedicineBrandOffering)
        .join(Medicine, MedicineBrandOffering.medicine_id == Medicine.id)
        .where(
            MedicineBrandOffering.id.in_(offering_ids),
            MedicineBrandOffering.is_deleted == False,  # noqa: E712
        )
    )
    for req in (await db.execute(stmt)).scalars():
        if req:
            return True
    return False


class AppliedCouponSchema(BaseModel):
    code: str = Field(..., max_length=50)
    discount_amount: float = Field(ge=0, description="Discount in rupees for this coupon")


class PaymentInitiateRequest(BaseModel):
    customer_name: str = Field(max_length=255)
    customer_phone: str = Field(max_length=15)
    customer_email: Optional[str] = Field(None, max_length=255)
    delivery_address: str
    pincode: Optional[str] = Field(None, max_length=10)
    city: Optional[str] = Field(None, max_length=100)
    items: List[CartItemSchema] = Field(min_length=1)
    subtotal: float = Field(ge=0)
    delivery_fee: float = Field(ge=0, default=0)
    discount_amount: float = Field(ge=0, default=0)
    final_amount: float = Field(gt=0)
    coupon_code: Optional[str] = None
    applied_coupons: Optional[List[AppliedCouponSchema]] = Field(None, description="Multiple coupons; discount_amount must equal sum of their discount_amount")
    prescription_path: Optional[str] = Field(
        None,
        max_length=2048,
        description="Path or URL from POST /upload (category=prescription); required when cart contains Rx medicines.",
    )


def _razorpay_key_mode(key_id: str) -> Literal["test", "live"]:
    return "test" if (key_id or "").startswith("rzp_test_") else "live"


class PaymentInitiateResponse(BaseModel):
    order_id: str  # UUID (for API/DB)
    order_reference: Optional[str] = None  # date_time_username (for display)
    razorpay_order_id: str
    key_id: str
    amount: int  # in paise
    razorpay_mode: Literal["test", "live"] = Field(
        ...,
        description="test when using Razorpay test keys (rzp_test_*), live otherwise",
    )


class VerifyPaymentRequest(BaseModel):
    razorpay_payment_id: str = Field(..., description="Razorpay payment ID from checkout")
    razorpay_order_id: str = Field(..., description="Razorpay order ID")
    razorpay_signature: str = Field(..., description="Razorpay signature from checkout")


class PaymentStatusResponse(BaseModel):
    order_id: str
    payment_status: str
    amount: Optional[float] = None
    transaction_id: Optional[str] = None
    order_status: Optional[str] = None


class RefundRequest(BaseModel):
    amount: Optional[float] = Field(None, description="Partial refund amount in rupees. Full refund if omitted.")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for refund")


class RefundResponse(BaseModel):
    order_id: str
    refund_status: str
    refund_amount: float
    refund_transaction_id: str


class MockInitiateResponse(BaseModel):
    order_id: str
    order_reference: Optional[str] = None
    amount: float  # in rupees (for display)


class MockCompleteRequest(BaseModel):
    order_id: str = Field(..., description="Order UUID from mock-initiate")


# ─── Endpoints ───


async def _fetch_active_delivery_settings(db: AsyncSession):
    ds_row = await db.execute(
        select(DeliverySetting)
        .where(DeliverySetting.is_deleted == False)
        .where(DeliverySetting.is_active == True)
        .order_by(DeliverySetting.created_at.desc())
    )
    return ds_row.scalars().first()


def _coupon_notes_line(data: PaymentInitiateRequest) -> Optional[str]:
    if data.applied_coupons:
        return "Coupons: " + ", ".join(ac.code for ac in data.applied_coupons)
    if data.coupon_code:
        return f"Coupon: {data.coupon_code}"
    return None


def _delivery_scheduling_note_line(ds: Optional[DeliverySetting]) -> Optional[str]:
    if not ds or not ds.is_enabled:
        return None
    raw = ds.delivery_slot_times
    parsed: object = []
    if raw:
        if isinstance(raw, str):
            try:
                parsed = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                parsed = []
        elif isinstance(raw, list):
            parsed = raw
    labels = slot_labels_from_parsed_items(parsed)
    meta = next_delivery_fulfillment_meta(labels, now=datetime.now(timezone.utc))
    return fulfillment_meta_to_order_note_line(meta)


def _merge_order_notes(data: PaymentInitiateRequest, ds: Optional[DeliverySetting]) -> Optional[str]:
    parts = [p for p in (_coupon_notes_line(data), _delivery_scheduling_note_line(ds)) if p]
    return " | ".join(parts) if parts else None


def _validate_checkout_amounts(data: PaymentInitiateRequest, ds: Optional[DeliverySetting]) -> None:
    """Ensure delivery fee and final amount match server rules (free-delivery band + delivery fee)."""
    if ds is not None and ds.is_enabled is False:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Delivery is currently turned off.")
    sub = Decimal(str(data.subtotal))
    expected_fee = delivery_fee_for_subtotal(sub, ds)
    got_fee = Decimal(str(data.delivery_fee))
    if abs(got_fee - expected_fee) > Decimal("0.02"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid delivery_fee: expected {float(expected_fee)}, got {data.delivery_fee}",
        )
    expected_final = (sub + expected_fee - Decimal(str(data.discount_amount))).quantize(Decimal("0.01"))
    got_final = Decimal(str(data.final_amount)).quantize(Decimal("0.01"))
    if abs(expected_final - got_final) > Decimal("0.02"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Amount mismatch: expected final_amount {float(expected_final)}, got {data.final_amount}",
        )


@router.post("/initiate", response_model=PaymentInitiateResponse)
async def initiate_razorpay_payment(
    data: PaymentInitiateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """
    Create order + order items + payment record, then create Razorpay order.
    Returns order_id, razorpay_order_id, key_id and amount for frontend checkout.
    """
    if not (settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment gateway (Razorpay) is not configured. Use mock-initiate for local testing or set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET.",
        )
    ip_address = get_client_ip(request)

    ds = await _fetch_active_delivery_settings(db)
    _validate_checkout_amounts(data, ds)

    phone_digits = "".join(c for c in data.customer_phone if c.isdigit())
    if len(phone_digits) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number. Must be at least 10 digits.",
        )

    try:
        oq = _offering_qty_from_cart_items(data.items)
        await inventory_service.validate_cart_stock(db, oq, current_user_id, ip_address)

        rx_needed = await _cart_requires_prescription_from_catalog(db, data.items)
        prescription_stored = _validated_prescription_path(data.prescription_path, required=rx_needed)

        # Resolve username for order_reference (date_time_username)
        user_row = await db.execute(
            select(User.full_name).where(User.id == current_user_id, User.is_deleted == False)
        )
        user_full_name = (user_row.scalar_one_or_none() or "") or data.customer_name or "user"
        username_slug = _slug_username(user_full_name)
        order_reference = _make_order_reference(username_slug)

        # 1. Create Order (id = UUID in DB; order_reference = date_time_username for display)
        order = Order(
            order_reference=order_reference,
            customer_id=current_user_id,
            customer_name=data.customer_name,
            customer_phone=data.customer_phone,
            customer_email=(data.customer_email or "").strip() or None,
            delivery_address=data.delivery_address,
            pincode=(data.pincode or "").strip() or None,
            city=(data.city or "").strip() or None,
            order_status="PENDING",
            total_amount=Decimal(str(data.subtotal)),
            discount_amount=Decimal(str(data.discount_amount)),
            delivery_fee=Decimal(str(data.delivery_fee)),
            final_amount=Decimal(str(data.final_amount)),
            payment_method="RAZORPAY",
            notes=_merge_order_notes(data, ds),
            prescription_path=prescription_stored,
            created_by=current_user_id,
            created_ip=ip_address,
        )
        db.add(order)
        await db.flush()

        # 2. Create OrderItems
        for item in data.items:
            brand_id = item.medicine_brand_id
            if brand_id and "_" in brand_id:
                brand_id = brand_id.split("_")[-1]
            if not brand_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing medicine_brand_id for item: {item.name}",
                )
            try:
                brand_uuid = UUID(brand_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid medicine_brand_id for item: {item.name}",
                )
            medicine_name_val, brand_name_val, rx_db = await _resolve_offering_for_order_item(db, brand_uuid)
            if brand_name_val is None and medicine_name_val is None:
                brand_name_val = item.name
            requires_rx_line = bool(rx_db) if rx_db is not None else bool(item.requires_prescription)

            order_item = OrderItem(
                order_id=order.id,
                medicine_brand_id=brand_uuid,
                medicine_name=medicine_name_val,
                brand_name=brand_name_val,
                quantity=item.quantity,
                unit_price=Decimal(str(item.price)),
                total_price=Decimal(str(round(item.price * item.quantity, 2))),
                requires_prescription=requires_rx_line,
                created_by=current_user_id,
                created_ip=ip_address,
            )
            db.add(order_item)

        await db.flush()

        if data.applied_coupons:
            for ac in data.applied_coupons:
                if not ac.code or ac.discount_amount <= 0:
                    continue
                code_upper = (ac.code or "").strip().upper()
                coupon_stmt = select(Coupon).where(
                    Coupon.code == code_upper,
                    Coupon.is_deleted == False,
                    Coupon.is_active == True,
                )
                coupon_result = await db.execute(coupon_stmt)
                coupon = coupon_result.scalar_one_or_none()
                if coupon:
                    usage = CouponUsage(
                        coupon_id=coupon.id,
                        order_id=order.id,
                        customer_id=current_user_id,
                        discount_amount=Decimal(str(ac.discount_amount)),
                        coupon_code=code_upper,
                        customer_name=(data.customer_name or "").strip() or None,
                        customer_phone=(data.customer_phone or "").strip() or None,
                        order_final_amount=Decimal(str(data.final_amount)),
                        created_by=current_user_id,
                        created_ip=ip_address,
                    )
                    db.add(usage)
                    coupon.usage_count = (coupon.usage_count or 0) + 1
            await db.flush()
        elif data.coupon_code and (data.coupon_code or "").strip() and data.discount_amount > 0:
            code_upper = (data.coupon_code or "").strip().upper()
            coupon_stmt = select(Coupon).where(
                Coupon.code == code_upper,
                Coupon.is_deleted == False,
                Coupon.is_active == True,
            )
            coupon_result = await db.execute(coupon_stmt)
            coupon = coupon_result.scalar_one_or_none()
            if coupon:
                usage = CouponUsage(
                    coupon_id=coupon.id,
                    order_id=order.id,
                    customer_id=current_user_id,
                    discount_amount=Decimal(str(data.discount_amount)),
                    coupon_code=code_upper,
                    customer_name=(data.customer_name or "").strip() or None,
                    customer_phone=(data.customer_phone or "").strip() or None,
                    order_final_amount=Decimal(str(data.final_amount)),
                    created_by=current_user_id,
                    created_ip=ip_address,
                )
                db.add(usage)
                coupon.usage_count = (coupon.usage_count or 0) + 1
                await db.flush()

        amount_paise = int(round(data.final_amount * 100))
        receipt = str(order.id)

        # 3. Create Razorpay order
        try:
            rz_order = razorpay_create_order(
                amount_paise=amount_paise,
                receipt=receipt,
                notes={"order_id": str(order.id)},
            )
        except Exception as e:
            await db.rollback()
            logger.error("Razorpay order create failed: %s", e, exc_info=True)
            # In dev, include exception details to speed up debugging.
            dev_detail = (
                f"Payment gateway error. Please try again. "
                f"(razorpay_create_order: {type(e).__name__}: {str(e)})"
                if _should_expose_exception_details(request)
                else "Payment gateway error. Please try again."
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=dev_detail,
            )

        razorpay_order_id = rz_order.get("id")
        if not razorpay_order_id:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Payment gateway did not return order ID.",
            )

        # 4. Create Payment record
        payment = Payment(
            order_id=order.id,
            payment_method="RAZORPAY",
            payment_status="INITIATED",
            amount=Decimal(str(data.final_amount)),
            merchant_transaction_id=receipt,
            gateway_order_id=razorpay_order_id,
            gateway_response=json.dumps(rz_order, default=str),
            created_by=current_user_id,
            created_ip=ip_address,
        )
        db.add(payment)
        await db.commit()

        logger.info("Razorpay payment initiated — order=%s, rz_order_id=%s, amount=₹%s", order.id, razorpay_order_id, data.final_amount)

        return PaymentInitiateResponse(
            order_id=str(order.id),
            order_reference=order.order_reference,
            razorpay_order_id=razorpay_order_id,
            key_id=settings.RAZORPAY_KEY_ID,
            amount=amount_paise,
            razorpay_mode=_razorpay_key_mode(settings.RAZORPAY_KEY_ID),
        )

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Error initiating payment: %s", e, exc_info=True)
        # In dev, include exception details to unblock UI testing.
        dev_detail = (
            f"Failed to initiate payment. Please try again. "
            f"({type(e).__name__}: {str(e)})"
            if _should_expose_exception_details(request)
            else "Failed to initiate payment. Please try again."
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=dev_detail,
        )


@router.post("/mock-initiate", response_model=MockInitiateResponse)
async def mock_initiate_payment(
    data: PaymentInitiateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """
    Create order + order items + payment record without Razorpay (for mock/demo).
    Frontend then shows mock payment screen; on "Proceed" call mock-complete.
    """
    ip_address = get_client_ip(request)

    ds = await _fetch_active_delivery_settings(db)
    _validate_checkout_amounts(data, ds)

    if data.applied_coupons:
        applied_sum = sum(ac.discount_amount for ac in data.applied_coupons)
        if abs(applied_sum - data.discount_amount) > 0.01:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Discount mismatch: applied_coupons sum {applied_sum} != discount_amount {data.discount_amount}",
            )
    phone_digits = "".join(c for c in data.customer_phone if c.isdigit())
    if len(phone_digits) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number. Must be at least 10 digits.",
        )
    try:
        oq = _offering_qty_from_cart_items(data.items)
        await inventory_service.validate_cart_stock(db, oq, current_user_id, ip_address)

        rx_needed = await _cart_requires_prescription_from_catalog(db, data.items)
        prescription_stored = _validated_prescription_path(data.prescription_path, required=rx_needed)

        user_row = await db.execute(
            select(User.full_name).where(User.id == current_user_id, User.is_deleted == False)
        )
        user_full_name = (user_row.scalar_one_or_none() or "") or data.customer_name or "user"
        username_slug = _slug_username(user_full_name)
        order_reference = _make_order_reference(username_slug)

        order = Order(
            order_reference=order_reference,
            customer_id=current_user_id,
            customer_name=data.customer_name,
            customer_phone=data.customer_phone,
            customer_email=(data.customer_email or "").strip() or None,
            delivery_address=data.delivery_address,
            pincode=(data.pincode or "").strip() or None,
            city=(data.city or "").strip() or None,
            order_status="PENDING",
            total_amount=Decimal(str(data.subtotal)),
            discount_amount=Decimal(str(data.discount_amount)),
            delivery_fee=Decimal(str(data.delivery_fee)),
            final_amount=Decimal(str(data.final_amount)),
            payment_method="RAZORPAY",
            notes=_merge_order_notes(data, ds),
            prescription_path=prescription_stored,
            created_by=current_user_id,
            created_ip=ip_address,
        )
        db.add(order)
        await db.flush()

        for item in data.items:
            brand_id = item.medicine_brand_id
            if brand_id and "_" in brand_id:
                brand_id = brand_id.split("_")[-1]
            if not brand_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing medicine_brand_id for item: {item.name}",
                )
            try:
                brand_uuid = UUID(brand_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid medicine_brand_id for item: {item.name}",
                )
            medicine_name_val, brand_name_val, rx_db = await _resolve_offering_for_order_item(db, brand_uuid)
            if brand_name_val is None and medicine_name_val is None:
                brand_name_val = item.name
            requires_rx_line = bool(rx_db) if rx_db is not None else bool(item.requires_prescription)
            order_item = OrderItem(
                order_id=order.id,
                medicine_brand_id=brand_uuid,
                medicine_name=medicine_name_val,
                brand_name=brand_name_val,
                quantity=item.quantity,
                unit_price=Decimal(str(item.price)),
                total_price=Decimal(str(round(item.price * item.quantity, 2))),
                requires_prescription=requires_rx_line,
                created_by=current_user_id,
                created_ip=ip_address,
            )
            db.add(order_item)
        await db.flush()

        if data.applied_coupons:
            for ac in data.applied_coupons:
                if not ac.code or ac.discount_amount <= 0:
                    continue
                code_upper = (ac.code or "").strip().upper()
                coupon_stmt = select(Coupon).where(
                    Coupon.code == code_upper,
                    Coupon.is_deleted == False,
                    Coupon.is_active == True,
                )
                coupon_result = await db.execute(coupon_stmt)
                coupon = coupon_result.scalar_one_or_none()
                if coupon:
                    usage = CouponUsage(
                        coupon_id=coupon.id,
                        order_id=order.id,
                        customer_id=current_user_id,
                        discount_amount=Decimal(str(ac.discount_amount)),
                        coupon_code=code_upper,
                        customer_name=(data.customer_name or "").strip() or None,
                        customer_phone=(data.customer_phone or "").strip() or None,
                        order_final_amount=Decimal(str(data.final_amount)),
                        created_by=current_user_id,
                        created_ip=ip_address,
                    )
                    db.add(usage)
                    coupon.usage_count = (coupon.usage_count or 0) + 1
            await db.flush()
        elif data.coupon_code and (data.coupon_code or "").strip() and data.discount_amount > 0:
            code_upper = (data.coupon_code or "").strip().upper()
            coupon_stmt = select(Coupon).where(
                Coupon.code == code_upper,
                Coupon.is_deleted == False,
                Coupon.is_active == True,
            )
            coupon_result = await db.execute(coupon_stmt)
            coupon = coupon_result.scalar_one_or_none()
            if coupon:
                usage = CouponUsage(
                    coupon_id=coupon.id,
                    order_id=order.id,
                    customer_id=current_user_id,
                    discount_amount=Decimal(str(data.discount_amount)),
                    coupon_code=code_upper,
                    customer_name=(data.customer_name or "").strip() or None,
                    customer_phone=(data.customer_phone or "").strip() or None,
                    order_final_amount=Decimal(str(data.final_amount)),
                    created_by=current_user_id,
                    created_ip=ip_address,
                )
                db.add(usage)
                coupon.usage_count = (coupon.usage_count or 0) + 1
                await db.flush()

        gateway_order_id_mock = "mock_" + str(order.id)
        payment = Payment(
            order_id=order.id,
            payment_method="RAZORPAY",
            payment_status="INITIATED",
            amount=Decimal(str(data.final_amount)),
            merchant_transaction_id=str(order.id),
            gateway_order_id=gateway_order_id_mock,
            gateway_response=json.dumps({"mock": True, "order_id": str(order.id)}, default=str),
            created_by=current_user_id,
            created_ip=ip_address,
        )
        db.add(payment)
        await db.commit()
        logger.info("Mock payment initiated — order=%s, amount=₹%s", order.id, data.final_amount)
        return MockInitiateResponse(
            order_id=str(order.id),
            order_reference=order.order_reference,
            amount=float(data.final_amount),
        )
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Error mock initiating payment: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order. Please try again.",
        )


@router.post("/mock-complete", response_model=PaymentStatusResponse)
async def mock_complete_payment(
    data: MockCompleteRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """
    Mark a mock-initiated order as paid (no real Razorpay). Call after user clicks Proceed on mock screen.
    """
    try:
        order_uuid = UUID(data.order_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order ID format.")
    result = await db.execute(
        select(Payment, Order).join(Order, Payment.order_id == Order.id).where(Payment.order_id == order_uuid)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order or payment not found.")
    payment, order = row
    if order.customer_id and order.customer_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this order.")
    if not payment.gateway_order_id or not str(payment.gateway_order_id).startswith("mock_"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This order is not a mock payment.")
    if payment.payment_status == "SUCCESS":
        return PaymentStatusResponse(
            order_id=str(order.id),
            payment_status="SUCCESS",
            amount=float(payment.amount),
            transaction_id=payment.gateway_transaction_id,
            order_status=order.order_status,
        )
    ip_address = get_client_ip(request)
    now_ist = datetime.now(IST)
    mock_txn_id = "mock_" + uuid4().hex[:12]
    try:
        await inventory_service.decrease_stock_for_order(db, order.id, current_user_id, ip_address)
        await db.execute(
            sa_update(Payment)
            .where(Payment.id == payment.id)
            .values(
                payment_status="SUCCESS",
                gateway_transaction_id=mock_txn_id,
                gateway_response=json.dumps({"mock": True, "completed_at": now_ist.isoformat()}, default=str),
                payment_date=now_ist,
                updated_by=current_user_id,
                updated_ip=ip_address,
            )
        )
        await db.execute(
            sa_update(Order)
            .where(Order.id == order.id)
            .values(
                order_status="CONFIRMED",
                payment_completed_at=now_ist,
                updated_by=current_user_id,
                updated_ip=ip_address,
            )
        )
        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise
    logger.info("Mock payment completed — order=%s", order.id)
    return PaymentStatusResponse(
        order_id=str(order.id),
        payment_status="SUCCESS",
        amount=float(payment.amount),
        transaction_id=mock_txn_id,
        order_status="CONFIRMED",
    )


@router.post("/verify", response_model=PaymentStatusResponse)
async def verify_razorpay_payment(
    data: VerifyPaymentRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """
    Verify Razorpay signature and update order/payment status.
    Call this from frontend after Razorpay checkout success.
    """
    if not verify_payment_signature(
        data.razorpay_order_id,
        data.razorpay_payment_id,
        data.razorpay_signature,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment signature.",
        )

    # Find payment by gateway_order_id (Razorpay order id)
    result = await db.execute(
        select(Payment, Order).join(Order, Payment.order_id == Order.id).where(
            Payment.gateway_order_id == data.razorpay_order_id,
        )
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    payment, order = row
    if order.customer_id and order.customer_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this order.")

    if payment.payment_status == "SUCCESS":
        return PaymentStatusResponse(
            order_id=str(order.id),
            payment_status="SUCCESS",
            amount=float(payment.amount),
            transaction_id=payment.gateway_transaction_id,
            order_status=order.order_status,
        )

    ip_address = get_client_ip(request)
    now_ist = datetime.now(IST)

    try:
        await inventory_service.decrease_stock_for_order(db, order.id, current_user_id, ip_address)
        await db.execute(
            sa_update(Payment)
            .where(Payment.id == payment.id)
            .values(
                payment_status="SUCCESS",
                gateway_transaction_id=data.razorpay_payment_id,
                gateway_response=json.dumps(
                    {"razorpay_payment_id": data.razorpay_payment_id, "verified": True},
                    default=str,
                ),
                payment_date=now_ist,
                updated_by=current_user_id,
                updated_ip=ip_address,
            )
        )
        await db.execute(
            sa_update(Order)
            .where(Order.id == order.id)
            .values(
                order_status="CONFIRMED",
                payment_completed_at=now_ist,
                updated_by=current_user_id,
                updated_ip=ip_address,
            )
        )
        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise

    logger.info("Razorpay payment verified — order=%s, payment_id=%s", order.id, data.razorpay_payment_id)

    return PaymentStatusResponse(
        order_id=str(order.id),
        payment_status="SUCCESS",
        amount=float(payment.amount),
        transaction_id=data.razorpay_payment_id,
        order_status="CONFIRMED",
    )


@router.get("/status/{order_id}", response_model=PaymentStatusResponse)
async def get_payment_status(
    order_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """Check payment status for an order. Used by callback page / polling."""
    try:
        order_uuid = UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order ID format.")

    result = await db.execute(select(Order).where(Order.id == order_uuid))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    if order.customer_id and order.customer_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this order.")

    result = await db.execute(select(Payment).where(Payment.order_id == order_uuid))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment record not found.")

    return PaymentStatusResponse(
        order_id=order_id,
        payment_status=payment.payment_status,
        amount=float(payment.amount),
        transaction_id=payment.gateway_transaction_id,
        order_status=order.order_status,
    )


@router.post("/refund/{order_id}", response_model=RefundResponse)
async def refund_payment(
    order_id: str,
    data: RefundRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("PAYMENT_PROCESS")),
):
    """Initiate a refund for a paid order. Admin only."""
    try:
        order_uuid = UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order ID format.")

    ip_address = get_client_ip(request)

    result = await db.execute(select(Order).where(Order.id == order_uuid))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    result = await db.execute(select(Payment).where(Payment.order_id == order_uuid))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment record not found.")

    if payment.payment_status != "SUCCESS":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot refund: payment status is {payment.payment_status}, expected SUCCESS.",
        )

    if payment.refund_status in ("INITIATED", "COMPLETED"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Refund already {payment.refund_status.lower()} for this order.",
        )

    refund_amount = Decimal(str(data.amount)) if data.amount else payment.amount
    if refund_amount > payment.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Refund amount (₹{refund_amount}) exceeds payment amount (₹{payment.amount}).",
        )

    razorpay_payment_id = payment.gateway_transaction_id
    if not razorpay_payment_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No gateway payment ID found for this order.",
        )

    amount_paise = None if refund_amount == payment.amount else int(round(float(refund_amount) * 100))
    refund_txn_id = str(uuid4()).replace("-", "")

    try:
        refund_response = process_refund(razorpay_payment_id, amount_paise)
        refund_id = refund_response.get("id", refund_txn_id)

        refund_status = "COMPLETED" if refund_response.get("status") == "processed" else "INITIATED"
        order_status = "REFUNDED" if refund_status == "COMPLETED" else "REFUND_INITIATED"

        await db.execute(
            sa_update(Payment)
            .where(Payment.id == payment.id)
            .values(
                refund_status=refund_status,
                refund_amount=refund_amount,
                refund_transaction_id=refund_id,
                gateway_response=json.dumps(refund_response, default=str),
                updated_by=current_user_id,
                updated_ip=ip_address,
            )
        )
        await db.execute(
            sa_update(Order)
            .where(Order.id == order_uuid)
            .values(
                order_status=order_status,
                updated_by=current_user_id,
                updated_ip=ip_address,
            )
        )
        await db.commit()

        logger.info("Refund processed — order=%s, refund_id=%s, amount=₹%s", order_id, refund_id, refund_amount)

        return RefundResponse(
            order_id=order_id,
            refund_status=refund_status,
            refund_amount=float(refund_amount),
            refund_transaction_id=refund_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error processing refund for order %s: %s", order_id, e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process refund. Please try again.",
        )
