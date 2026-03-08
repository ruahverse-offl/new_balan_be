# Inventory and Product Batches — What They Are and How They Help the Admin

This doc explains **Product Batches** and **Inventory (Inventory Transactions)** in the pharmacy system, and how they help the admin run the shop.

---

## 1. What is a **Product Batch**?

A **Product Batch** is one physical lot of a medicine brand that you have in stock. Each batch has:

| Field | Meaning |
|-------|--------|
| **medicine_brand_id** | Which product (e.g. "Paracetamol 500mg – Brand X") this batch is for |
| **batch_number** | Your internal or manufacturer batch id (e.g. `BATCH-0925`, `LOT-2025-001`) |
| **expiry_date** | When this batch expires (important for FEFO and compliance) |
| **purchase_price** | Cost price per unit (₹) when you bought this batch |
| **quantity_available** | How many units of this batch are currently in stock |

**Why batches?**  
- Same medicine brand can be bought at different times → different expiry dates and cost prices.  
- You need to track **which lot** was sold (for recalls, audits, expiry).  
- Stock is tracked **per batch**; total stock for a product = sum of all its batches’ `quantity_available`.

**Where the admin uses it:**  
- **Admin → Product Batches:** Create, edit, delete batches (add new stock, set batch number, expiry, purchase price, quantity).  
- When you **approve an order**, the system automatically picks a batch (FEFO), reduces its `quantity_available`, and links that batch to the order line.

---

## 2. What is **Inventory** (Inventory Transactions)?

**Inventory** in this app means the **history of stock movements**: every time stock goes **in** or **out**, a row is stored in **inventory_transactions**.

Each transaction has:

| Field | Meaning |
|-------|--------|
| **medicine_brand_id** | Which product |
| **product_batch_id** | Which batch was affected |
| **transaction_type** | e.g. `PURCHASE` (stock in), `SALE` (stock out), `ADJUSTMENT_IN`, `ADJUSTMENT_OUT` |
| **quantity_change** | Positive = stock added, negative = stock removed |
| **reference_order_id** | If this was a sale, the order id (optional) |
| **remarks** | Free text (e.g. "New purchase", "Order approved - sold 2 units") |

So:  
- **Product Batches** = current snapshot of stock (per batch: how many units, expiry, cost).  
- **Inventory Transactions** = log of **how** that stock changed (who added/removed, when, why).

**Where the admin uses it:**  
- **Admin → Inventory:** List all movements, add manual transactions (e.g. new purchase, adjustment), edit/delete if needed.  
- When you add a **PURCHASE** (or adjustment in), the backend updates the chosen batch’s `quantity_available` and creates this transaction.  
- When you **approve an order**, the backend creates **SALE** transactions (negative quantity) and decreases the batch stock.

---

## 3. How they work together

1. **Admin adds stock**  
   - Create a **Product Batch** (medicine brand + batch number + expiry + purchase price + quantity), **or**  
   - Create an **Inventory Transaction** of type **PURCHASE** (select batch, positive quantity) → batch’s `quantity_available` increases.

2. **Customer places order**  
   - Order is created with **order_items** (medicine_brand_id, quantity, etc.). No batch is chosen yet.

3. **Admin approves order**
   - For each order line, the system:  
     - Finds a **batch** of that medicine brand with enough `quantity_available` (FEFO: first expiry, first out).  
     - **Reduces that batch’s `quantity_available`** by the sold quantity (so both the batch and the inventory log stay in sync).  
     - Sets **order_item.product_batch_id** to that batch (for audit/recalls).  
     - Creates an **Inventory Transaction** of type **SALE** with negative quantity and `reference_order_id` = this order.  
   So: **both** the product batch quantity **and** the inventory (transaction history) are updated—the batch is the live stock; the transaction is the record of the sale.

4. **Admin sees what’s in stock and what moved**  
   - **Product Batches** → current stock per batch (and expiry, cost).  
   - **Inventory** → full history of ins and outs (purchases, sales, adjustments).

---

## 4. How this helps the admin

| Need | How it’s helped |
|------|-----------------|
| **Know what’s in stock** | Product Batches show `quantity_available` per batch; dashboard can show total stock per product and value (quantity × purchase_price). |
| **Avoid selling expired medicine** | Batches have **expiry_date**; order approval uses **FEFO** (first expiry, first out). Inventory dashboard can show **expiring soon** and **expired** alerts. |
| **Trace which batch was sold** | Each order item can store **product_batch_id**; inventory has SALE transactions with **reference_order_id**. So you can trace a sale back to batch and order. |
| **Record new stock (purchases)** | Add a new **Product Batch** or an **Inventory Transaction** (PURCHASE) so batch quantity and history are correct. |
| **Adjust stock (damage, count correction)** | Use **Inventory** with transaction type like ADJUSTMENT_IN / ADJUSTMENT_OUT; batch quantity is updated and the change is logged. |
| **See value of stock** | Inventory dashboard uses batches (quantity_available × purchase_price) to show **total stock value**, top products by value, etc. |
| **Low stock / out of stock** | Dashboard can compare batch quantities to thresholds and show **low stock** and **out of stock** alerts so admin can reorder. |
| **Audit and compliance** | Every movement is in **inventory_transactions** (who, when, type, quantity, batch, optional order reference). |

---

## 5. Summary

- **Product Batches** = “How much of each lot do I have?” (batch number, expiry, cost, quantity).  
- **Inventory (transactions)** = “How did stock change?” (purchases, sales, adjustments, linked to batch and optionally to order).  
- **Admin** uses Batches to manage current stock and expiry, and Inventory to record and review all movements; when orders are approved, the system uses batches (FEFO) and writes SALE transactions so stock and history stay correct and traceable.
