# Role permissions guide – why staff see no data

Customer and home screens work because they use endpoints that either don’t require special permissions or use the customer’s own data. **Staff roles (customer_service, manager, cashier, admin) see empty Orders/Payments/Dashboard because the backend returns 403 when their role does not have the right permissions.** The frontend then shows empty lists (it catches errors and uses `items: []`).

## How it works

- **Orders list** (`GET /api/v1/orders`):  
  - If the user has **ORDER_VIEW**, they see **all** orders.  
  - If not, they only see orders where `customer_id` = their user id (i.e. only their own orders). Staff usually don’t place orders, so they see nothing.

- **Payments list** (`GET /api/v1/payments`):  
  - User must have **ORDER_VIEW** or **PAYMENT_PROCESS**.  
  - If the role has neither, the API returns 403 and the frontend shows an empty payments list.

- **Statistics KPIs** (`GET /api/v1/kpi/summary`):  
  - Requires **DASHBOARD_VIEW**.  
  - Without it, 403 and no KPI data.

So: **no wrong field names and no wrong API paths** – the APIs and response shapes are correct. The issue is **missing role–permission assignments** in the database.

## Permissions that affect staff screens

| Permission code     | Used for |
|---------------------|----------|
| **ORDER_VIEW**      | List all orders, view order detail, and (after backend change) list/view payments |
| **ORDER_UPDATE**    | Change order status, approval, etc. |
| **PAYMENT_PROCESS** | Create/update payments, refunds; also allows list/view payments |
| **DASHBOARD_VIEW**  | KPI summary (`/api/v1/kpi/summary`) for the admin Statistics tab |

Other permissions (e.g. DOCTOR_VIEW, MEDICINE_VIEW, STAFF_VIEW, COUPON_VIEW, etc.) control their respective admin tabs the same way.

## What to do in the database

1. **Identify your staff role names**  
   In the **`M_roles`** table, note the `name` (and `id`) for: admin, manager, cashier, customer_service (or whatever you use). The backend returns `role_code` as `M_roles.name`.

2. **Ensure permissions exist**  
   In the **`M_permissions`** table there should be rows with `code` equal to at least:
   - `ORDER_VIEW`
   - `ORDER_UPDATE`
   - `PAYMENT_PROCESS`
   - `DASHBOARD_VIEW`

3. **Assign permissions to staff roles**  
   In **`M_role_permissions`**, link each staff role to the right permissions. For example, for a role that should see and work with orders and payments and dashboards, attach:
   - ORDER_VIEW
   - ORDER_UPDATE
   - PAYMENT_PROCESS (and/or rely on ORDER_VIEW for list/view payments)
   - DASHBOARD_VIEW  

   So: **admin** typically gets all of these; **manager/cashier/customer_service** should at least get **ORDER_VIEW** and **DASHBOARD_VIEW** so they see orders and dashboards; give **PAYMENT_PROCESS** and **ORDER_UPDATE** where they are allowed to process payments or change order status.

### Example SQL (adjust role names/IDs to match your DB)

```sql
-- List current roles and permissions (for reference)
SELECT r.name AS role_name, p.code AS permission_code
FROM "M_roles" r
JOIN "M_role_permissions" rp ON rp.role_id = r.id AND rp.is_deleted = false
JOIN "M_permissions" p ON p.id = rp.permission_id AND p.is_deleted = false
ORDER BY r.name, p.code;

-- Example: grant ORDER_VIEW, ORDER_UPDATE, PAYMENT_PROCESS, DASHBOARD_VIEW to role named 'manager'
-- (Replace <manager_role_id> and <permission_id_*> with actual UUIDs from your DB.)
-- Insert into "M_role_permissions" (role_id, permission_id, created_by, created_at, created_ip, is_deleted, …)
-- for each permission you want to add. created_by can be a system user UUID; created_ip e.g. '0.0.0.0'.
```

Use your admin UI (Roles/Permissions/RolePermissions tabs) or run similar SQL to attach the permission IDs to the correct role IDs.

## Backend change already made

- **Payments list and get-by-id** now allow users who have **either** `PAYMENT_PROCESS` **or** `ORDER_VIEW`. So any role that can see orders (ORDER_VIEW) can also see the payments list and payment details without needing PAYMENT_PROCESS. Create/update/refund still require PAYMENT_PROCESS.

## Admin sidebar (`M_menu_tasks` / `M_role_task_grants`)

`GET /api/v1/auth/me/permissions` returns **`menu_items`**: objects built from the database (`M_menu_tasks` joined with `M_role_task_grants` for the user’s role). A task appears only if **`show_in_menu`** and **`can_read`** are true for that role. Each task also has **`can_create`**, **`can_update`**, **`can_delete`** for future task-level checks; API routes still use `require_permission` today.

**`menu_keys`** is still returned as the list of task **`code`** strings (same as each item’s `code`) for backward compatibility.

To add a new admin tab: insert a **`M_menu_tasks`** row (`code` must match the React tab id) and grant rows per role in **`M_role_task_grants`**. Icons use **`icon_key`** (Lucide export name) mapped on the frontend.

## Quick check

1. Log in as a staff user (e.g. manager/cashier).
2. Open browser DevTools → Network.
3. Go to Admin → Orders or Payments.
4. Check the request to `/api/v1/orders` or `/api/v1/payments`:
   - **403** → role is missing the required permission(s). Add ORDER_VIEW (and DASHBOARD_VIEW for dashboards) in the DB as above.
   - **200** with `items: []` → no orders/payments in the database yet; permissions are fine.
   - **200** with `items: [...]` → data is loading correctly.

After assigning ORDER_VIEW (and DASHBOARD_VIEW, ORDER_UPDATE, PAYMENT_PROCESS as needed) to the relevant roles, staff should see orders, payments, and dashboards as intended.
