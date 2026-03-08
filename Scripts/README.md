# Database Scripts

Scripts for managing the New Balan Medical database. All scripts must be run from the `backend/` directory.

## Quick Start (New Developer)

```bash
# From the backend/ directory

# Step 1: Install dependencies
pip install -r requirements.txt

# Step 2: Seed RBAC data (roles, permissions, users)
PYTHONIOENCODING=utf-8 python Scripts/seed_rbac_data.py

# Step 3: Seed operational data (medicines, doctors, orders, etc.)
PYTHONIOENCODING=utf-8 python Scripts/seed_all_data.py
```

> **Windows CMD users:** Replace `PYTHONIOENCODING=utf-8 python` with:
> ```
> set PYTHONIOENCODING=utf-8
> python Scripts/seed_rbac_data.py
> ```

---

## Scripts Overview

| Script | Purpose | Destructive? |
|--------|---------|:---:|
| `seed_rbac_data.py` | Seeds roles, permissions, users | Yes - deletes existing RBAC data |
| `seed_all_data.py` | Seeds all operational/sample data | No - additive only |
| `delete_all_data.py` | Deletes all operational data (keeps RBAC) | Yes - requires confirmation |

---

## seed_rbac_data.py

Seeds the RBAC (Role-Based Access Control) system. **Run this FIRST** before any other seed script.

**What it creates:**

| Table | Count | Details |
|-------|:-----:|---------|
| roles | 7 | DEV_ADMIN, ADMIN, MANAGER, PHARMACIST, CASHIER, CUSTOMER_SERVICE, CUSTOMER |
| permissions | 59 | 12 RBAC + 47 operational permissions |
| role_permissions | ~170 | Maps permissions to each role |
| users | 7 | One user per role |

**Login credentials** (all passwords: `NewBalan@2026`):

| Email | Role | Access |
|-------|------|--------|
| devadmin@newbalan.com | DEV_ADMIN | Full access + RBAC management |
| admin@newbalan.com | ADMIN | Full operational access |
| manager@newbalan.com | MANAGER | Store management |
| pharmacist@newbalan.com | PHARMACIST | Prescription review, orders |
| cashier@newbalan.com | CASHIER | Order processing, payments |
| customerservice@newbalan.com | CUSTOMER_SERVICE | Appointments, test bookings |
| customer@newbalan.com | CUSTOMER | Shopping, booking |

**Usage:**
```bash
PYTHONIOENCODING=utf-8 python Scripts/seed_rbac_data.py
```

**Warning:** This script DELETES all existing users, roles, permissions, and role-permission mappings before re-creating them.

---

## seed_all_data.py

Seeds all operational tables with sample data. **Requires** `seed_rbac_data.py` to be run first (needs existing users and roles).

**What it creates:**

| Table | Count | Details |
|-------|:-----:|---------|
| therapeutic_categories | 10 | Antibiotics, Analgesics, Vitamins, etc. |
| medicines | 10 | Paracetamol, Ibuprofen, Amoxicillin, etc. |
| medicine_compositions | 10 | Salt name, strength, unit per medicine |
| medicine_brands | 20 | 2 brands per medicine (Crocin, Dolo 650, etc.) |
| doctors | 3 | General Physician, Cardiologist, Pediatrician |
| polyclinic_tests | 5 | Blood Test, ECG, X-Ray, etc. |
| product_categories | 4 | OTC, Prescription, Daily Care, Wellness |
| coupons | 3 | SAVE5, SAVE10, WELCOME |
| delivery_settings | 1 | Delivery config with zones |
| delivery_slots | 5 | Time slots (10AM-8PM) |
| pharmacist_profiles | 1 | License info for pharmacist user |
| product_batches | 30 | 2 batches per brand |
| orders | 20 | Mixed statuses (PENDING, DELIVERED, etc.) |
| order_items | ~60 | 1-5 items per order |
| payments | ~17 | For non-cancelled orders |
| inventory_transactions | ~15 | Purchase and sale records |
| appointments | 15 | Mixed statuses |
| test_bookings | 10 | Mixed statuses |
| coupon_usages | ~5 | Sample coupon usage records |

**Usage:**
```bash
PYTHONIOENCODING=utf-8 python Scripts/seed_all_data.py
```

---

## delete_all_data.py

Deletes ALL operational data while preserving RBAC tables (roles, permissions, users).

**What it deletes:** All tables listed in `seed_all_data.py` above.

**What it preserves:** roles, permissions, role_permissions, users.

**Usage:**
```bash
# Interactive (asks for confirmation)
PYTHONIOENCODING=utf-8 python Scripts/delete_all_data.py

# Skip confirmation
PYTHONIOENCODING=utf-8 python Scripts/delete_all_data.py --yes
```

---

## Full Reset (Nuclear Option)

To completely reset and re-seed everything:

```bash
# Step 1: Delete operational data
PYTHONIOENCODING=utf-8 python Scripts/delete_all_data.py --yes

# Step 2: Re-seed RBAC (deletes and recreates users/roles)
PYTHONIOENCODING=utf-8 python Scripts/seed_rbac_data.py

# Step 3: Re-seed operational data
PYTHONIOENCODING=utf-8 python Scripts/seed_all_data.py
```

Or drop and recreate the database entirely:

```bash
# In psql:
DROP DATABASE new_balan;
CREATE DATABASE new_balan;

# Then start the backend (auto-creates tables):
PYTHONIOENCODING=utf-8 uvicorn main:app --reload

# Then seed:
PYTHONIOENCODING=utf-8 python Scripts/seed_rbac_data.py
PYTHONIOENCODING=utf-8 python Scripts/seed_all_data.py
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Make sure you're in `backend/` directory and dependencies are installed (`pip install -r requirements.txt`) |
| Unicode/emoji errors | Use `PYTHONIOENCODING=utf-8` prefix (or `set PYTHONIOENCODING=utf-8` on Windows CMD) |
| Database connection error | Check `DATABASE_URL` in `.env` file |
| `Role 'X' not found` in seed_all_data | Run `seed_rbac_data.py` first |
| Foreign key constraint errors | Run `delete_all_data.py` before re-seeding |
| `psql` not found | Add PostgreSQL `bin/` to your system PATH |
