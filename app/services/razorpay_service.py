"""
Razorpay Payment Gateway Service
Handles order creation, payment verification, and refunds.
"""

import logging
import razorpay
from razorpay.errors import SignatureVerificationError
from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Singleton Razorpay client
_razorpay_client: razorpay.Client | None = None


def get_razorpay_client() -> razorpay.Client:
    """Get or create the Razorpay client singleton."""
    global _razorpay_client
    if _razorpay_client is None:
        if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
            raise ValueError("RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET must be set")
        _razorpay_client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        logger.info("Razorpay client initialized (key_id=%s)", settings.RAZORPAY_KEY_ID[:8] + "...")
    return _razorpay_client


def create_order(amount_paise: int, receipt: str, notes: dict | None = None) -> dict:
    """
    Create a Razorpay order.

    Args:
        amount_paise: Amount in paise (₹100 = 10000)
        receipt: Merchant receipt/reference ID (e.g. our order UUID)
        notes: Optional dict of key-value notes

    Returns:
        dict: Razorpay order response with 'id' (razorpay_order_id)
    """
    client = get_razorpay_client()
    data = {
        "amount": amount_paise,
        "currency": "INR",
        "receipt": (receipt or "rcpt")[:64],
    }
    if notes:
        data["notes"] = notes
    order = client.order.create(data)
    logger.info(
        "Razorpay order created — receipt=%s, amount=%d paise, order_id=%s",
        receipt, amount_paise, order.get("id"),
    )
    return order


def verify_payment_signature(
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
) -> bool:
    """
    Verify Razorpay payment signature after successful payment.

    Args:
        razorpay_order_id: Order ID from Razorpay
        razorpay_payment_id: Payment ID from Razorpay
        razorpay_signature: Signature from checkout success handler

    Returns:
        bool: True if signature is valid
    """
    try:
        client = get_razorpay_client()
        params = {
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
        }
        client.utility.verify_payment_signature(params)
        logger.info("Razorpay signature verified — order_id=%s, payment_id=%s", razorpay_order_id, razorpay_payment_id)
        return True
    except SignatureVerificationError as e:
        logger.warning("Razorpay signature verification failed: %s", e)
        return False


def fetch_payment(payment_id: str) -> dict | None:
    """
    Fetch payment details from Razorpay.

    Args:
        payment_id: Razorpay payment ID

    Returns:
        dict or None: Payment details including status
    """
    try:
        client = get_razorpay_client()
        payment = client.payment.fetch(payment_id)
        return payment
    except Exception as e:
        logger.warning("Razorpay fetch payment failed for %s: %s", payment_id, e)
        return None


def process_refund(payment_id: str, amount_paise: int | None = None) -> dict:
    """
    Initiate a refund on Razorpay. Full refund if amount_paise is None.

    Args:
        payment_id: Razorpay payment ID
        amount_paise: Refund amount in paise, or None for full refund

    Returns:
        dict: Razorpay refund response
    """
    client = get_razorpay_client()
    payload = {}
    if amount_paise is not None:
        payload["amount"] = amount_paise
    refund = client.payment.refund(payment_id, payload)
    logger.info(
        "Razorpay refund initiated — payment_id=%s, amount_paise=%s, refund_id=%s",
        payment_id, amount_paise, refund.get("id"),
    )
    return refund
