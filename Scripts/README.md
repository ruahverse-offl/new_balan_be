# Database scripts

Utilities in this folder are run manually when needed (from the **backend project root**, with the virtual environment activated).

## Schema

Application tables are created by **SQLAlchemy `create_all`** when the API starts (`M_*` masters, `T_*` transactions).

PostgreSQL-only **order fulfillment** column/status patches run automatically from `app/db/order_fulfillment_schema.py` after `create_all`.

## One-off helpers

- **`apply_order_fulfillment_columns.py`** — runs the same fulfillment patches as the API (optional if you do not want to start the server).

- **`drop_product_categories_and_screens.sql`** / **`.py`** — legacy cleanup for removed product-category tables.

## Roles and access

See **`ACCESS_AND_ROLES.md`** at the backend root for role definitions, the module matrix, and copy-paste **bootstrap SQL**.

### Demo seed (RBAC + users + catalog + orders)

**`seed_demo_data.py`** loads roles, modules, the full RBAC matrix (aligned with `ACCESS_AND_ROLES.md`), five staff/customer users, **4** medicine categories, **4** brands, **10** medicines (each with an offering + inventory), and **20** orders at varied lifecycle statuses.

From **`new_balan_be`** (venv active, `DATABASE_URL` in `.env`):

```bash
# First time on an empty database (creates tables, then seeds):
python Scripts/seed_demo_data.py --create-tables

# Normal run (tables already exist):
python Scripts/seed_demo_data.py

# Re-run after a previous seed (deletes DEMO-* catalog, demo users, DEMO-SEED-* orders, then re-inserts):
python Scripts/seed_demo_data.py --force

# Dev reset: empty ALL application tables (PostgreSQL TRUNCATE CASCADE; SQLite deletes all rows), then seed:
python Scripts/seed_demo_data.py --wipe-db
```

| Email | Role | Password |
|-------|------|----------|
| `admin@newbalan.com` | ADMIN | `NewBalan@2026` |
| `devadmin@newbalan.com` | DEV_ADMIN | same |
| `manager@newbalan.com` | MANAGER | same |
| `deliveryagent@newbalan.com` | DELIVERY_AGENT | same |
| `customer@newbalan.com` | CUSTOMER | same |

Demo catalog names are prefixed with **`DEMO`**; order references are **`DEMO-SEED-01`** … **`DEMO-SEED-20`** so `--force` can target them safely.
