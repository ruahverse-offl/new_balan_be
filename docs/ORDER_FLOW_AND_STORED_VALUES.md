# Order flow: start to end — and what we store (including UUIDs)

This doc describes the full flow of placing an order and **how** we store the **order** and **UUID references**, and **what values** go into the database.

---

## 1. Start: where the UUIDs and order data come from

### Frontend (cart)

- User adds medicines from **Pharmacy** or **Medicine Detail**.
- Each cart item is built with:
  - **`id`** — used as cart line id (often same as `medicine_brands.id` or a composite key).
  - **`brandId`** — set from **`brand.id`** (the **medicine_brands.id** UUID from the API).
  - `name`, `price`, `quantity`, `requires_prescription` / `requiresPrescription`.
- Cart is kept in **CartContext** and persisted in **localStorage** (`nb_cart`).

So the **medicine reference** we care about for storage is the **medicine_brands.id** UUID, sent as **`medicine_brand_id`** at checkout.

### Checkout payload (what the frontend sends)

When the user clicks Pay, the frontend builds **orderData** and calls **POST `/api/v1/razorpay/initiate`**:

```js
// frontend/src/pages/Checkout.jsx (conceptual)
orderData = {
  customer_name, customer_phone, customer_email,
  delivery_address, pincode, city,
  items: cart.map(item => ({
    medicine_brand_id: item.brandId || item.id || null,  // ← UUID of medicine_brands.id
    name: item.name,
    quantity: item.quantity,
    price: item.price,
    requires_prescription: item.requires_prescription || item.requiresPrescription || false,
  })),
  subtotal, delivery_fee, discount_amount, final_amount,
  coupon_code: appliedDiscount > 0 ? formData.coupon : null,
  prescription_id: null,
};
```

So we **do** send and later store:

- A **UUID reference** per line: **`medicine_brand_id`** = `medicine_brands.id`.
- The **order** is created on the backend from this payload (we don’t send an order id; backend generates it).

---

## 2. Backend: how we store the order and UUIDs

Backend receives **PaymentInitiateRequest** and runs this flow.

### Step 1 — Create one **Order** row (UUID generated here)

- **Table:** `orders`
- **Who generates the UUID:** Database (PostgreSQL `gen_random_uuid()`) for **`orders.id`** (and same for all other `id` columns below).
- **What we set:**

| We store (column)        | Value we store |
|--------------------------|----------------|
| **id**                   | New UUID (auto, primary key). |
| **customer_id**          | **current_user_id** (UUID from JWT → `users.id`). |
| customer_name            | `data.customer_name` |
| customer_phone           | `data.customer_phone` |
| customer_email           | `data.customer_email` (trimmed) or null |
| delivery_address         | `data.delivery_address` |
| pincode, city            | From request (trimmed) or null |
| order_source             | `"ONLINE"` |
| order_status             | `"PENDING"` |
| approval_status          | `"PENDING"` |
| total_amount             | `data.subtotal` |
| discount_amount          | `data.discount_amount` |
| delivery_fee             | `data.delivery_fee` |
| final_amount             | `data.final_amount` |
| payment_method           | `"RAZORPAY"` |
| prescription_id          | `data.prescription_id` or null |
| notes                    | e.g. `"Coupon: DEMO20"` if coupon used, else null |
| created_by               | **current_user_id** (UUID) |
| created_at, created_ip   | Server/time, IP |

So **we are storing**:

- The **order** as one row with a new **order UUID**.
- The **user reference** as **customer_id** = `users.id` (UUID).

After `db.add(order)` and `flush`, **order.id** is available (the new order UUID).

---

### Step 2 — Create **OrderItem** rows (one per cart line); here we store the medicine UUID and order reference

- **Table:** `order_items`
- For **each** `data.items` entry:

**1) Resolve `medicine_brand_id` (the UUID we store):**

- Backend takes `item.medicine_brand_id` (string from frontend).
- If it contains `"_"`, it takes the part **after** the last `"_"` (to support composite keys like `medicineId_brandId`).
- It parses that as **UUID** and validates it exists in DB:

  - `MedicineBrand.id == brand_uuid`, `MedicineBrand.is_deleted == False`
  - Joined with **Medicine** to read **medicine name** and **brand name** for snapshot.

**2) What we store in `order_items`:**

| We store (column)        | Value we store |
|--------------------------|----------------|
| **id**                   | New UUID (auto). |
| **order_id**             | **order.id** (UUID of the row we just created in `orders`). |
| **medicine_brand_id**    | **brand_uuid** (the validated `medicine_brands.id` UUID). |
| medicine_name            | From DB: `Medicine.name` (snapshot at order time). |
| brand_name               | From DB: `MedicineBrand.brand_name`, or fallback `item.name`. |
| quantity                 | `item.quantity` |
| unit_price               | `item.price` |
| total_price              | `unit_price * quantity` (rounded). |
| requires_prescription    | `item.requires_prescription` |
| product_batch_id         | null (can be set later on approval/fulfilment). |
| created_by               | **current_user_id** (UUID). |
| created_at, created_ip   | Server/time, IP. |

So **we are storing**:

- **UUID reference to the order:** **order_id** = `orders.id`.
- **UUID reference to the product:** **medicine_brand_id** = `medicine_brands.id`.
- Snapshot of **medicine_name** and **brand_name** so the order line is readable even if master data changes.

---

### Step 3 — Optional: **CouponUsage** (if coupon applied)

- **Table:** `coupon_usages`
- We store:

| We store (column)   | Value we store |
|---------------------|----------------|
| **id**              | New UUID (auto). |
| **coupon_id**       | **coupon.id** (UUID from `coupons` table, looked up by `data.coupon_code`). |
| **order_id**        | **order.id** (same order UUID). |
| **customer_id**     | **current_user_id** (UUID). |
| discount_amount     | `data.discount_amount` |
| coupon_code         | Snapshot of code (e.g. `"DEMO20"`). |
| customer_name, customer_phone, order_final_amount | Snapshots from request. |
| created_by, created_at, created_ip | Audit. |

So **we are storing**:

- **UUID references:** **coupon_id** (`coupons.id`), **order_id** (`orders.id`), **customer_id** (`users.id`).

We also increment **coupon.usage_count** by 1.

---

### Step 4 — Razorpay order + one **Payment** row

- Backend creates a Razorpay order (external API) with amount in paise and **receipt = str(order.id)** (our order UUID as string).
- **Table:** `payments`

| We store (column)           | Value we store |
|-----------------------------|----------------|
| **id**                      | New UUID (auto). |
| **order_id**                | **order.id** (UUID). |
| payment_method              | `"RAZORPAY"` |
| payment_status              | `"INITIATED"` |
| amount                      | `data.final_amount` |
| merchant_transaction_id     | **receipt** = `str(order.id)` (our order UUID). |
| gateway_order_id            | Razorpay order id (string). |
| gateway_transaction_id      | null until verify. |
| gateway_response            | Full Razorpay JSON (audit). |
| payment_date                | null until verify. |
| refund_*                    | Defaults (NONE, 0, null). |
| created_by, created_at, created_ip | Audit. |

So **we are storing**:

- **UUID reference to the order:** **order_id** = `orders.id`.

Then backend **commits** the transaction and returns to frontend: **order_id** (our UUID), **razorpay_order_id**, **key_id**, **amount**.

---

## 3. Frontend: Razorpay UI and verify

- Frontend opens Razorpay checkout with **order_id** (our UUID) and **razorpay_order_id**.
- User pays; Razorpay returns **razorpay_payment_id** and **razorpay_signature**.
- Frontend calls **POST `/api/v1/razorpay/verify`** with:
  - `razorpay_payment_id`, `razorpay_order_id`, `razorpay_signature`.

---

## 4. Backend: verify — what we update (no new UUIDs, same order)

- Find **Payment** by **gateway_order_id** = `razorpay_order_id`, and its **Order**.
- Verify signature; then **update** (no new order, same UUIDs):

**Payments table:**

- **payment_status** = `"SUCCESS"`
- **gateway_transaction_id** = `razorpay_payment_id`
- **payment_date** = now
- **gateway_response** = updated JSON

**Orders table:**

- **order_status** = `"CONFIRMED"`
- **payment_completed_at** = now

So from start to end we **keep the same order UUID**; we only update status and payment fields.

---

## 5. Summary: UUID references and order storage

- **Order:** Stored in **`orders`** with a new **UUID** generated by the DB. We don’t send an order id from frontend; backend creates it and returns it.
- **User reference:** Stored as **customer_id** = `users.id` (UUID) on **orders** and **coupon_usages**, and as **created_by** on orders, order_items, payments, coupon_usages.
- **Product reference:** Each line is stored in **`order_items`** with **medicine_brand_id** = `medicine_brands.id` (UUID from frontend, validated and optionally normalized from composite string). We also store **order_id** = `orders.id` (UUID).
- **Coupon reference:** If a coupon is used, we store in **`coupon_usages`** **coupon_id** = `coupons.id` (UUID), **order_id** = `orders.id` (UUID), **customer_id** = `users.id` (UUID).
- **Payment reference:** One **`payments`** row per initiate with **order_id** = `orders.id` (UUID), and **merchant_transaction_id** = that same order UUID as string.

So **we are storing** the **order** (with its own UUID) and **all UUID references** (user, order, medicine brand, coupon, and payment linked to order) as described above; the **values** we store are either from the request, from the DB (snapshots), or server-generated (ids, timestamps, IPs).
