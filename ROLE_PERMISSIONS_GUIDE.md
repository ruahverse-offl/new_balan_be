# Role permissions guide – why staff see no data

Customer and home screens work because they use endpoints that either don’t require special permissions or use the customer’s own data. **Staff roles (customer_service, manager, cashier, admin) see empty Orders/Payments/Dashboard because the backend returns 403 when their role does not have the right permissions.** The frontend then shows empty lists (it catches errors and uses `items: []`).

## How it works

- **Orders list** (`GET /api/v1/orders`):  
  - If the user has **ORDER_VIEW**, they see **all** orders.  
  - If not, they only see orders where `customer_id` = their user id (i.e. only their own orders). Staff usually don’t place orders, so they see nothing.

- **Payments list** (`GET /api/v1/payments`):  
  - User must have **ORDER_VIEW** or **PAYMENT_PROCESS**.  
  - If the role has neither, the API returns 403 and the frontend shows an empty payments list.

- **Dashboards** (e.g. `GET /api/v1/dashboards/orders`, finance, inventory, sales):  
  - Require **DASHBOARD_VIEW**.  
  - Without it, 403 and no dashboard data.

So: **no wrong field names and no wrong API paths** – the APIs and response shapes are correct. The issue is **missing role–permission assignments** in the database.

## Permissions that affect staff screens

| Permission code     | Used for |
|---------------------|----------|
| **ORDER_VIEW**      | List all orders, view order detail, and (after backend change) list/view payments |
| **ORDER_UPDATE**    | Change order status, approval, etc. |
| **PAYMENT_PROCESS** | Create/update payments, refunds; also allows list/view payments |
| **DASHBOARD_VIEW**  | All dashboard APIs (orders, finance, inventory, sales) |

Other permissions (e.g. DOCTOR_VIEW, MEDICINE_VIEW, STAFF_VIEW, COUPON_VIEW, etc.) control their respective admin tabs the same way.

## What to do in the database

1. **Identify your staff role names**  
   In the `roles` table, note the `name` (and `id`) for: admin, manager, cashier, customer_service (or whatever you use). The backend returns `role_code` as `roles.name`.

2. **Ensure permissions exist**  
   In the `permissions` table there should be rows with `code` equal to at least:
   - `ORDER_VIEW`
   - `ORDER_UPDATE`
   - `PAYMENT_PROCESS`
   - `DASHBOARD_VIEW`

3. **Assign permissions to staff roles**  
   In `role_permissions`, link each staff role to the right permissions. For example, for a role that should see and work with orders and payments and dashboards, attach:
   - ORDER_VIEW
   - ORDER_UPDATE
   - PAYMENT_PROCESS (and/or rely on ORDER_VIEW for list/view payments)
   - DASHBOARD_VIEW  

   So: **admin** typically gets all of these; **manager/cashier/customer_service** should at least get **ORDER_VIEW** and **DASHBOARD_VIEW** so they see orders and dashboards; give **PAYMENT_PROCESS** and **ORDER_UPDATE** where they are allowed to process payments or change order status.

### Example SQL (adjust role names/IDs to match your DB)

```sql
-- List current roles and permissions (for reference)
SELECT r.name AS role_name, p.code AS permission_code
FROM roles r
JOIN role_permissions rp ON rp.role_id = r.id AND rp.is_deleted = false
JOIN permissions p ON p.id = rp.permission_id AND p.is_deleted = false
ORDER BY r.name, p.code;

-- Example: grant ORDER_VIEW, ORDER_UPDATE, PAYMENT_PROCESS, DASHBOARD_VIEW to role named 'manager'
-- (Replace <manager_role_id> and <permission_id_*> with actual UUIDs from your DB.)
-- You need to insert into role_permissions (role_id, permission_id, created_by, created_at, created_ip, is_deleted)
-- for each permission you want to add. created_by can be a system user UUID; created_ip e.g. '0.0.0.0'.
```

Use your admin UI (Roles/Permissions/RolePermissions tabs) or run similar SQL to attach the permission IDs to the correct role IDs.

## Backend change already made

- **Payments list and get-by-id** now allow users who have **either** `PAYMENT_PROCESS` **or** `ORDER_VIEW`. So any role that can see orders (ORDER_VIEW) can also see the payments list and payment details without needing PAYMENT_PROCESS. Create/update/refund still require PAYMENT_PROCESS.

## Seed script (recommended)

A script is provided to assign the required permissions to staff roles in one go:

```bash
# From the backend directory
cd backend
python seed_roles_permissions.py
```

This will:

- Ensure permissions `ORDER_VIEW`, `DASHBOARD_VIEW`, `ORDER_UPDATE`, `PAYMENT_PROCESS` exist in the `permissions` table.
- Assign these permissions to staff roles (admin, manager, cashier, customer_service, and any other non-CUSTOMER role).

After running it, staff users should see Orders, Payments, and Dashboards. You can still adjust role-permission links later via the Admin → Role Permissions UI.

## Quick check

1. Log in as a staff user (e.g. manager/cashier).
2. Open browser DevTools → Network.
3. Go to Admin → Orders or Payments.
4. Check the request to `/api/v1/orders` or `/api/v1/payments`:
   - **403** → role is missing the required permission(s). Add ORDER_VIEW (and DASHBOARD_VIEW for dashboards) in the DB as above.
   - **200** with `items: []` → no orders/payments in the database yet; permissions are fine.
   - **200** with `items: [...]` → data is loading correctly.

After assigning ORDER_VIEW (and DASHBOARD_VIEW, ORDER_UPDATE, PAYMENT_PROCESS as needed) to the relevant roles, staff should see orders, payments, and dashboards as intended.
