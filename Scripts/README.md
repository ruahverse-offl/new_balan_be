# Database scripts

Utilities in this folder are run manually when needed (from the backend project root, with the virtual environment activated).

## One-off SQL / Python helpers

- **`drop_product_categories_and_screens.sql`** / **`.py`** — legacy cleanup for removed product-category tables.

Application schema is created by **SQLAlchemy `create_all`** on startup (tables prefixed **`M_`** for master data and **`T_`** for transactions).

## Seed data

- **`seed_database.py`** — optional RBAC, default users, menu tasks/grants, and sample master/transaction rows. Run from the backend project root: `python Scripts/seed_database.py` (see script docstring for `--reset` and `--password`).
