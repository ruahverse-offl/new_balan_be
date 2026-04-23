# Access model: roles and module matrix

This document describes **who can do what** using **`M_roles`**, **`M_modules`**, and **`M_module_role_permissions`**.  
Protected routes use the matrix via [`has_module_action`](app/utils/rbac.py) / [`require_module_action`](app/utils/rbac.py). The `/auth/me/permissions` **permissions** array uses synthetic labels (e.g. `ORDER_VIEW`) **derived** from the same matrix in `app/utils/rbac.py` for the frontend — there is no separate `rbac_permission_map` module.

**Runtime check:** For the authenticated user, read **`M_users.role_id`**, load the row in **`M_module_role_permissions`** for that **`role_id`** and the **`M_modules`** row (match on `name`, e.g. `doctors`). For an action such as **create**, allow the request only if **`can_create`** is true on that matrix row (and the row/module/user/role are active, not soft-deleted). [`has_module_action`](app/utils/rbac.py) implements this. Use [`require_module_action`](app/utils/rbac.py) or [`require_any_module_action`](app/utils/rbac.py) on routes.

**Roles in use (6):** `ADMIN`, `DEV_ADMIN`, `MANAGER`, `DELIVERY_AGENT`, `PUBLIC`, `CUSTOMER`.

Create tables (`create_all` on startup), then either apply the SQL below, use the admin UI (**App modules**, **Role × module access**), or run **`Scripts/seed_demo_data.py`** for a full demo (RBAC + sample users + catalog + 20 orders) — see **`Scripts/README.md`**.

---

## Contents

1. [Roles](#roles-canonical-m_rolesname)
2. [Module × CRUD matrix](#who-gets-what-module--crud)
3. [Storefront checkout & orders](#storefront-checkout--orders)
4. [Frontend / JWT behaviour](#frontend--jwt-behaviour)
5. [Bootstrap SQL (PostgreSQL)](#bootstrap-sql-postgresql)
6. [Current user API (`GET /api/v1/auth/me/permissions`)](#current-user-api-get-apiv1authmepermissions)
7. [Related implementation files](#related-implementation-files)
8. [Operational notes](#operational-notes)

---

## Roles (canonical `M_roles.name`)

| Role | Purpose |
|------|--------|
| **ADMIN** | Full operational control **except** the three RBAC screens: `roles`, `access-modules`, `role-access` (those are **DEV_ADMIN** only). |
| **DEV_ADMIN** | RBAC administration only: roles, app modules, role×module matrix. |
| **MANAGER** | Full **CRUD** on every **operational** module (same modules as **ADMIN**), excluding the three RBAC screens above. |
| **DELIVERY_AGENT** | Delivery queue: orders **assigned to this user**; lifecycle updates (e.g. delivered) per `orders` / `order_lifecycle` rules. |
| **PUBLIC** | Preferred **self-signup** storefront account. **Read:** medicines, medicine categories, inventory (stock context), brand master; **create/read** orders (logged-in) and coupon usages. Same matrix as **CUSTOMER**. **No admin sidebar** from the permissions API (see [Current user API](#current-user-api-get-apiv1authmepermissions)). |
| **CUSTOMER** | **End customer who places orders** — legacy role name kept for older databases. Same storefront matrix and API rules as **PUBLIC**. Registration in [`auth_service`](app/services/auth_service.py) assigns **PUBLIC** if that role exists, otherwise **CUSTOMER** (see also `GET /api/v1/auth/customer-role-id`). |

---

## Who gets what (module × CRUD)

Columns: **C** = create, **R** = read, **U** = update, **D** = delete.  
**PUBLIC** and **CUSTOMER** use the **same** grants; the matrix shows one column labelled **PUBLIC**.

| Module (`M_modules.name`) | ADMIN | DEV_ADMIN | MANAGER | DELIVERY_AGENT | PUBLIC |
|---------------------------|:-----:|:---------:|:-------:|:--------------:|:------:|
| roles | — | CRUD | — | — | — |
| access-modules | — | CRUD | — | — | — |
| role-access | — | CRUD | — | — | — |
| doctors | CRUD | — | CRUD | — | — |
| medicines | CRUD | — | CRUD | — | R |
| therapeutic-categories | CRUD | — | CRUD | — | R |
| inventory | CRUD | — | CRUD | — | R |
| brand-master | CRUD | — | CRUD | — | R |
| orders | CRUD | — | CRUD | — | C+R |
| delivery-orders | CRUD | — | CRUD | — | — |
| appointments | CRUD | — | CRUD | — | — |
| delivery | CRUD | — | CRUD | — | — |
| coupons | CRUD | — | CRUD | — | — |
| staff | CRUD | — | CRUD | — | — |
| test-bookings | CRUD | — | CRUD | — | — |
| payments | CRUD | — | CRUD | — | — |
| coupon-usages | CRUD | — | CRUD | — | C+R |

- The **Statistics / KPI** admin screen and **`dashboard`** module were removed.  
- **Sidebar order** for staff comes from **`M_modules.display_order`** and is returned on each `menu_items[]` entry (and via each item’s `displayOrder`).

**DELIVERY_AGENT:** `delivery-orders` **R+U** satisfies legacy `DELIVERY_ORDER_VIEW` / `DELIVERY_ORDER_UPDATE`. List scoping (only assigned orders) is enforced in **`orders_router`** / services, not only by the matrix.

**Coupon definitions vs coupon usages:** Staff work on coupons via **`COUPON_*`** → **`coupons`** module. Recording/listing **usage** rows uses **`COUPON_USAGE_*`** → **`coupon-usages`** module; `GET`/`POST` **`/api/v1/coupon-usages`** also accept legacy **`COUPON_VIEW`** / **`COUPON_CREATE`** so existing staff grants keep working.

---

## Storefront checkout & orders

Applies to **PUBLIC** and **CUSTOMER** (and is enforced in [`orders_router`](app/routes/orders_router.py)):

| Rule | Detail |
|------|--------|
| **JWT required** | `POST /api/v1/orders/` uses `Depends(get_current_user_id)` — **no anonymous guest checkout**. |
| **`ORDER_CREATE`** | Required for every authenticated order create (matrix: `orders.can_create`). |
| **`customer_id`** | Must **equal** the JWT subject (`sub`) for **PUBLIC** / **CUSTOMER** so users cannot place orders for another account. Staff roles may still create orders on behalf of others when their matrix allows it. |

**Matrix shorthand for storefront (PUBLIC / CUSTOMER):**

| Module | Flags | Synthetic codes (examples) |
|--------|-------|-----------------------------|
| **medicines** | R | `MEDICINE_VIEW` |
| **therapeutic-categories** | R | `MEDICINE_CATEGORY_VIEW` |
| **inventory** | R | `INVENTORY_VIEW` (e.g. stock context; `GET /api/v1/inventory/stock` may stay unauthenticated) |
| **brand-master** | R | `BRAND_MASTER_VIEW` |
| **orders** | C+R | `ORDER_CREATE`, `ORDER_VIEW`, `ORDER_DETAIL_VIEW` |
| **coupon-usages** | C+R | `COUPON_USAGE_CREATE`, `COUPON_USAGE_VIEW` |

Public list/detail routes for medicines, categories, brands, and stock may still be open without JWT; matrix read grants keep **`GET /api/v1/auth/me/permissions`** aligned for logged-in customers and any future gated reads.

---

## Frontend / JWT behaviour

- **`ADMIN`:** Operational super-user in some UI checks (`isAdminUser` in `Admin.jsx`). Does **not** imply `DEV_ADMIN`.
- **`DEV_ADMIN`:** Sidebar title from **`role_display_name`** on `GET /api/v1/auth/me/permissions`. Matrix should only grant RBAC modules.
- **`PUBLIC` / `CUSTOMER`:** Treated as **non-staff** in the SPA ([`roles.js`](../new_balan_fe/src/utils/roles.js) — `isStaffUser` / `isStaffRoleCode`) so storefront matrix rows never send users to the **Admin** portal.
- **Staff user management:** Dropdowns exclude **PUBLIC** and **CUSTOMER** so storefront accounts are not assigned staff roles by mistake.

---

## Bootstrap SQL (PostgreSQL)

Run after tables exist. Replace audit actor `00000000-0000-0000-0000-000000000001` with a real `M_users.id` when available.

### 1) Roles

```sql
INSERT INTO "M_roles" (name, description, created_by, created_ip, is_deleted, is_active)
SELECT 'ADMIN', 'Operational admin; no RBAC tabs.', '00000000-0000-0000-0000-000000000001'::uuid, '127.0.0.1', false, true
WHERE NOT EXISTS (SELECT 1 FROM "M_roles" WHERE name = 'ADMIN');

INSERT INTO "M_roles" (name, description, created_by, created_ip, is_deleted, is_active)
SELECT 'DEV_ADMIN', 'RBAC administration only.', '00000000-0000-0000-0000-000000000001'::uuid, '127.0.0.1', false, true
WHERE NOT EXISTS (SELECT 1 FROM "M_roles" WHERE name = 'DEV_ADMIN');

INSERT INTO "M_roles" (name, description, created_by, created_ip, is_deleted, is_active)
SELECT 'MANAGER', 'Operational manager; full CRUD on non-RBAC modules.', '00000000-0000-0000-0000-000000000001'::uuid, '127.0.0.1', false, true
WHERE NOT EXISTS (SELECT 1 FROM "M_roles" WHERE name = 'MANAGER');

INSERT INTO "M_roles" (name, description, created_by, created_ip, is_deleted, is_active)
SELECT 'DELIVERY_AGENT', 'Assigned deliveries only.', '00000000-0000-0000-0000-000000000001'::uuid, '127.0.0.1', false, true
WHERE NOT EXISTS (SELECT 1 FROM "M_roles" WHERE name = 'DELIVERY_AGENT');

INSERT INTO "M_roles" (name, description, created_by, created_ip, is_deleted, is_active)
SELECT 'PUBLIC', 'Storefront self-signup; orders require login.', '00000000-0000-0000-0000-000000000001'::uuid, '127.0.0.1', false, true
WHERE NOT EXISTS (SELECT 1 FROM "M_roles" WHERE name = 'PUBLIC');

INSERT INTO "M_roles" (name, description, created_by, created_ip, is_deleted, is_active)
SELECT 'CUSTOMER', 'End customer who places orders (legacy; same matrix as PUBLIC).', '00000000-0000-0000-0000-000000000001'::uuid, '127.0.0.1', false, true
WHERE NOT EXISTS (SELECT 1 FROM "M_roles" WHERE name = 'CUSTOMER');
```

### 2) Modules (sidebar / RBAC keys — must match `M_modules.name` and route checks in `app/utils/rbac.py`)

```sql
INSERT INTO "M_modules" (name, display_name, is_menu_item, parent_module_id, display_order, icon_key, created_by, created_ip, is_deleted, is_active)
SELECT v.name, v.dname, true, NULL, v.ord, v.icon, '00000000-0000-0000-0000-000000000001'::uuid, '127.0.0.1', false, true
FROM (VALUES
  ('roles', 'Roles', 5, 'Shield'),
  ('access-modules', 'App modules', 6, 'Layers'),
  ('role-access', 'Role × module access', 7, 'Grid3x3'),
  ('doctors', 'Manage Doctors', 10, 'Users'),
  ('medicines', 'Manage Medicines', 20, 'Pill'),
  ('therapeutic-categories', 'Medicine Cat.', 25, 'Tags'),
  ('inventory', 'Inventory', 26, 'Package'),
  ('brand-master', 'Brand catalog', 27, 'Tag'),
  ('orders', 'Orders', 30, 'ShoppingCart'),
  ('delivery-orders', 'My deliveries', 31, 'Truck'),
  ('appointments', 'Appointments', 40, 'Clock'),
  ('delivery', 'Delivery Settings', 50, 'Truck'),
  ('coupons', 'Coupons & Marquee', 60, 'Ticket'),
  ('staff', 'Manage Staff', 70, 'UserCheck'),
  ('test-bookings', 'Test Bookings', 80, 'Calendar'),
  ('payments', 'Payments', 90, 'CreditCard'),
  ('coupon-usages', 'Coupon Usages', 100, 'BarChart3')
) AS v(name, dname, ord, icon)
WHERE NOT EXISTS (SELECT 1 FROM "M_modules" m WHERE m.name = v.name);
```

### 3) Matrix grants (core pattern)

**ADMIN** — all modules **except** the three RBAC screens, full CRUD:

```sql
INSERT INTO "M_module_role_permissions" (
  module_id, role_id, can_create, can_read, can_update, can_delete,
  created_by, created_ip, is_deleted, is_active
)
SELECT m.id, r.id, true, true, true, true,
       '00000000-0000-0000-0000-000000000001'::uuid, '127.0.0.1', false, true
FROM "M_modules" m
JOIN "M_roles" r ON r.name = 'ADMIN'
WHERE m.name NOT IN ('roles', 'access-modules', 'role-access')
  AND NOT EXISTS (
    SELECT 1 FROM "M_module_role_permissions" x
    WHERE x.module_id = m.id AND x.role_id = r.id AND x.is_deleted = false
  );
```

**DEV_ADMIN** — RBAC modules only (full CRUD):

```sql
INSERT INTO "M_module_role_permissions" (
  module_id, role_id, can_create, can_read, can_update, can_delete,
  created_by, created_ip, is_deleted, is_active
)
SELECT m.id, r.id, true, true, true, true,
       '00000000-0000-0000-0000-000000000001'::uuid, '127.0.0.1', false, true
FROM "M_modules" m
JOIN "M_roles" r ON r.name = 'DEV_ADMIN'
WHERE m.name IN ('roles', 'access-modules', 'role-access')
  AND NOT EXISTS (
    SELECT 1 FROM "M_module_role_permissions" x
    WHERE x.module_id = m.id AND x.role_id = r.id AND x.is_deleted = false
  );
```

**MANAGER** — full **CRUD** on all modules **except** the three RBAC screens (same operational footprint as **ADMIN**):

```sql
INSERT INTO "M_module_role_permissions" (
  module_id, role_id, can_create, can_read, can_update, can_delete,
  created_by, created_ip, is_deleted, is_active
)
SELECT m.id, r.id, true, true, true, true,
       '00000000-0000-0000-0000-000000000001'::uuid, '127.0.0.1', false, true
FROM "M_modules" m
JOIN "M_roles" r ON r.name = 'MANAGER'
WHERE m.name NOT IN ('roles', 'access-modules', 'role-access')
  AND NOT EXISTS (
    SELECT 1 FROM "M_module_role_permissions" x
    WHERE x.module_id = m.id AND x.role_id = r.id AND x.is_deleted = false
  );
```

**DELIVERY_AGENT** — `delivery-orders` read + update:

```sql
INSERT INTO "M_module_role_permissions" (
  module_id, role_id, can_create, can_read, can_update, can_delete,
  created_by, created_ip, is_deleted, is_active
)
SELECT m.id, r.id, false, true, true, false,
       '00000000-0000-0000-0000-000000000001'::uuid, '127.0.0.1', false, true
FROM "M_modules" m
JOIN "M_roles" r ON r.name = 'DELIVERY_AGENT'
WHERE m.name = 'delivery-orders'
  AND NOT EXISTS (SELECT 1 FROM "M_module_role_permissions" x WHERE x.module_id = m.id AND x.role_id = r.id AND x.is_deleted = false);
```

**PUBLIC** and **CUSTOMER** — storefront matrix (`menu_items` is still **empty** for these roles in the API; see `get_sidebar_menu_items` in `app/utils/rbac.py`):

```sql
-- medicines: catalog read (MEDICINE_VIEW)
INSERT INTO "M_module_role_permissions" (
  module_id, role_id, can_create, can_read, can_update, can_delete,
  created_by, created_ip, is_deleted, is_active
)
SELECT m.id, r.id, false, true, false, false,
       '00000000-0000-0000-0000-000000000001'::uuid, '127.0.0.1', false, true
FROM "M_modules" m
JOIN "M_roles" r ON r.name IN ('PUBLIC', 'CUSTOMER')
WHERE m.name = 'medicines'
  AND NOT EXISTS (SELECT 1 FROM "M_module_role_permissions" x WHERE x.module_id = m.id AND x.role_id = r.id AND x.is_deleted = false);

-- therapeutic-categories: browse categories (MEDICINE_CATEGORY_VIEW)
INSERT INTO "M_module_role_permissions" (
  module_id, role_id, can_create, can_read, can_update, can_delete,
  created_by, created_ip, is_deleted, is_active
)
SELECT m.id, r.id, false, true, false, false,
       '00000000-0000-0000-0000-000000000001'::uuid, '127.0.0.1', false, true
FROM "M_modules" m
JOIN "M_roles" r ON r.name IN ('PUBLIC', 'CUSTOMER')
WHERE m.name = 'therapeutic-categories'
  AND NOT EXISTS (SELECT 1 FROM "M_module_role_permissions" x WHERE x.module_id = m.id AND x.role_id = r.id AND x.is_deleted = false);

-- inventory: read stock context (INVENTORY_VIEW)
INSERT INTO "M_module_role_permissions" (
  module_id, role_id, can_create, can_read, can_update, can_delete,
  created_by, created_ip, is_deleted, is_active
)
SELECT m.id, r.id, false, true, false, false,
       '00000000-0000-0000-0000-000000000001'::uuid, '127.0.0.1', false, true
FROM "M_modules" m
JOIN "M_roles" r ON r.name IN ('PUBLIC', 'CUSTOMER')
WHERE m.name = 'inventory'
  AND NOT EXISTS (SELECT 1 FROM "M_module_role_permissions" x WHERE x.module_id = m.id AND x.role_id = r.id AND x.is_deleted = false);

-- brand-master: read shared brand catalog (BRAND_MASTER_VIEW)
INSERT INTO "M_module_role_permissions" (
  module_id, role_id, can_create, can_read, can_update, can_delete,
  created_by, created_ip, is_deleted, is_active
)
SELECT m.id, r.id, false, true, false, false,
       '00000000-0000-0000-0000-000000000001'::uuid, '127.0.0.1', false, true
FROM "M_modules" m
JOIN "M_roles" r ON r.name IN ('PUBLIC', 'CUSTOMER')
WHERE m.name = 'brand-master'
  AND NOT EXISTS (SELECT 1 FROM "M_module_role_permissions" x WHERE x.module_id = m.id AND x.role_id = r.id AND x.is_deleted = false);

-- orders: create + read (ORDER_CREATE + ORDER_VIEW / ORDER_DETAIL_VIEW)
INSERT INTO "M_module_role_permissions" (
  module_id, role_id, can_create, can_read, can_update, can_delete,
  created_by, created_ip, is_deleted, is_active
)
SELECT m.id, r.id, true, true, false, false,
       '00000000-0000-0000-0000-000000000001'::uuid, '127.0.0.1', false, true
FROM "M_modules" m
JOIN "M_roles" r ON r.name IN ('PUBLIC', 'CUSTOMER')
WHERE m.name = 'orders'
  AND NOT EXISTS (SELECT 1 FROM "M_module_role_permissions" x WHERE x.module_id = m.id AND x.role_id = r.id AND x.is_deleted = false);

-- coupon-usages: record + list (COUPON_USAGE_CREATE / COUPON_USAGE_VIEW)
INSERT INTO "M_module_role_permissions" (
  module_id, role_id, can_create, can_read, can_update, can_delete,
  created_by, created_ip, is_deleted, is_active
)
SELECT m.id, r.id, true, true, false, false,
       '00000000-0000-0000-0000-000000000001'::uuid, '127.0.0.1', false, true
FROM "M_modules" m
JOIN "M_roles" r ON r.name IN ('PUBLIC', 'CUSTOMER')
WHERE m.name = 'coupon-usages'
  AND NOT EXISTS (SELECT 1 FROM "M_module_role_permissions" x WHERE x.module_id = m.id AND x.role_id = r.id AND x.is_deleted = false);
```

---

## Current user API (`GET /api/v1/auth/me/permissions`)

Used after login (or session refresh) to drive the admin SPA and permission checks.

| Field | Meaning |
|-------|--------|
| `role_code` | `M_roles.name` (e.g. `ADMIN`, `PUBLIC`). |
| `role_display_name` | Short UI label derived from the role name. |
| `role_description` | Optional `M_roles.description`. |
| `menu_items` / `menuItems` | Modules with `is_menu_item` and `can_read`. Each: `code`, `displayName` (or `display_name`), `displayOrder`, `iconKey`, and **`grants`**: `canCreate`, `canRead`, `canUpdate`, `canDelete` from `M_module_role_permissions`. **Always `[]` for `PUBLIC` and `CUSTOMER`.** Order is the sidebar order; parallel `menu_keys` / `menu_order` are not returned (derive from `menuItems` if needed). |

Legacy **`dashboard`**, **`DASHBOARD_VIEW`**, and **`GET /api/v1/kpi/summary`** are not used.

---

## Related implementation files

| Area | Location |
|------|----------|
| Matrix checks, `get_sidebar_menu_items`, `require_module_action` | `app/utils/rbac.py` |
| Me / permissions response | `app/routes/auth_router.py` (`GET /api/v1/auth/me/permissions`) |
| Order create rules (JWT, `ORDER_CREATE`, `customer_id`) | `app/routes/orders_router.py` |
| Coupon usage routes (usage vs staff coupon codes) | `app/routes/coupon_usages_router.py` |
| Signup role resolution (PUBLIC vs CUSTOMER) | `app/services/auth_service.py`, `GET /api/v1/auth/customer-role-id` |
| SPA staff vs customer | [`../new_balan_fe/src/utils/roles.js`](../new_balan_fe/src/utils/roles.js) |
| Backend permission → frontend tab key | [`../new_balan_fe/src/utils/permissionMapper.js`](../new_balan_fe/src/utils/permissionMapper.js) |

---

## Operational notes

- **Order DDL patches** (extra `T_orders` columns, status enum clean-up) run from **`app/db/order_fulfillment_schema.py`** on API startup for PostgreSQL — not tied to removed `migrations/*.sql` files.
- **`Scripts/apply_order_fulfillment_columns.py`** can apply fulfillment DDL without starting the full app.
