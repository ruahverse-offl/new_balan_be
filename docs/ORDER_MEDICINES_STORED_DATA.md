# What Gets Stored When a User Orders Medicines

When a customer places a medicine order (checkout → Pay → Razorpay), the backend stores data in **four places**: `orders`, `order_items`, `payments`, and optionally `coupon_usages`.

---

## 1. **`orders`** table (one row per order)

| Column | Source | Description |
|--------|--------|-------------|
| **id** | Auto (UUID) | Order ID |
| **customer_id** | Logged-in user | `users.id` (who placed the order) |
| **customer_name** | Checkout form | Customer name |
| **customer_phone** | Checkout form | Phone number |
| **customer_email** | Checkout form | Email (optional) |
| **delivery_address** | Checkout form | Full delivery address |
| **pincode** | Checkout form | Optional |
| **city** | Checkout form | Optional |
| **order_source** | Fixed | `"ONLINE"` |
| **order_status** | Fixed at create | `"PENDING"` (updated after payment) |
| **approval_status** | Fixed at create | `"PENDING"` |
| **total_amount** | Request | Cart subtotal (before discount/delivery) |
| **discount_amount** | Request | Coupon discount in ₹ |
| **delivery_fee** | Request | Delivery fee in ₹ |
| **final_amount** | Request | Amount customer pays (subtotal − discount + delivery_fee) |
| **payment_method** | Fixed | `"RAZORPAY"` |
| **payment_completed_at** | Set on verify | When payment succeeded (null until then) |
| **prescription_id** | Request | Optional prescription reference |
| **notes** | Generated | e.g. `"Coupon: DEMO20"` if coupon used |
| **processed_by** | Set later | Staff who processed (optional) |
| **created_by, created_at, created_ip** | Audit | Who/when/where |
| **updated_by, updated_at, updated_ip** | Audit | Optional |
| **is_deleted** | Default false | Soft delete |

---

## 2. **`order_items`** table (one row per medicine line in the cart)

For **each item** in the cart:

| Column | Source | Description |
|--------|--------|-------------|
| **id** | Auto (UUID) | Order item ID |
| **order_id** | From new order | Links to `orders.id` |
| **medicine_brand_id** | Cart item | `medicine_brands.id` (which product) |
| **medicine_name** | Lookup from DB | From `medicines.name` via brand (snapshot) |
| **brand_name** | Lookup / cart | From `medicine_brands.brand_name` or item name (snapshot) |
| **quantity** | Cart item | Number of units |
| **unit_price** | Cart item | Price per unit at order time |
| **total_price** | Calculated | `unit_price × quantity` |
| **requires_prescription** | Cart item | Whether this item needs prescription |
| **product_batch_id** | Set later | Batch used for fulfilment (optional, can be set on approval) |
| **created_by, created_at, created_ip** | Audit | Who/when/where |

So for each medicine line you store: which brand, its name/brand name at order time, qty, unit price, total, and prescription flag.

---

## 3. **`payments`** table (one row when payment is initiated)

| Column | Source | Description |
|--------|--------|-------------|
| **id** | Auto (UUID) | Payment record ID |
| **order_id** | From new order | Links to `orders.id` |
| **payment_method** | Fixed | `"RAZORPAY"` |
| **payment_status** | At create | `"INITIATED"` (updated to SUCCESS/FAILED on verify) |
| **amount** | Request | `final_amount` in ₹ |
| **merchant_transaction_id** | Our ref | Same as `order.id` (receipt) |
| **gateway_order_id** | Razorpay | Razorpay order ID |
| **gateway_transaction_id** | Set on verify | Razorpay payment_id |
| **gateway_response** | Razorpay | Full JSON response (audit) |
| **payment_date** | Set on verify | When payment completed |
| **refund_status** | Default | `"NONE"` (updated if refunded) |
| **refund_amount** | Default 0 | Refunded amount |
| **refund_transaction_id** | Razorpay | Refund ID if any |
| **created_by, created_at, created_ip** | Audit | Who/when/where |

---

## 4. **`coupon_usages`** table (one row only if a coupon was applied)

Created only when the request has a valid **coupon_code** and **discount_amount > 0**:

| Column | Source | Description |
|--------|--------|-------------|
| **id** | Auto (UUID) | Usage record ID |
| **coupon_id** | Lookup by code | `coupons.id` |
| **order_id** | From new order | `orders.id` |
| **customer_id** | Logged-in user | `users.id` |
| **discount_amount** | Request | Discount in ₹ |
| **coupon_code** | Request | Snapshot of code (e.g. DEMO20) |
| **customer_name** | Request | Snapshot |
| **customer_phone** | Request | Snapshot |
| **order_final_amount** | Request | Snapshot of final amount |
| **created_by, created_at, created_ip** | Audit | Who/when/where |

The coupon’s **usage_count** is also incremented by 1.

---

## Request payload (what the frontend sends)

The frontend calls **POST `/api/v1/razorpay/initiate`** with a body like:

```json
{
  "customer_name": "Customer Name",
  "customer_phone": "9876543210",
  "customer_email": "customer@example.com",
  "delivery_address": "123 Street, City",
  "pincode": "560001",
  "city": "Bangalore",
  "items": [
    {
      "medicine_brand_id": "uuid-of-medicine-brand",
      "name": "Paracetamol 500mg - Brand X",
      "quantity": 2,
      "price": 45.50,
      "requires_prescription": false
    }
  ],
  "subtotal": 91.00,
  "delivery_fee": 40.00,
  "discount_amount": 0,
  "final_amount": 131.00,
  "coupon_code": null,
  "prescription_id": null
}
```

From this, the backend creates the **orders**, **order_items**, **payments**, and (if applicable) **coupon_usages** rows as above.

---

## Flow summary

1. **POST /razorpay/initiate** with customer info, cart items, amounts, optional coupon.
2. Backend creates **Order** → **OrderItem** per cart line (with medicine/brand snapshot) → optional **CouponUsage** → Razorpay order → **Payment** (INITIATED) → commit.
3. After user pays, frontend calls **POST /razorpay/verify**; backend updates **Payment** (status, gateway_transaction_id, payment_date) and **Order** (order_status, payment_completed_at).

All medicine-order data is therefore stored in **orders**, **order_items**, **payments**, and optionally **coupon_usages**.
