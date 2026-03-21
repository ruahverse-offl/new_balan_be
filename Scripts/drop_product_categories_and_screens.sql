-- Run against your PostgreSQL database (e.g. psql -f ... or pgAdmin query tool).
-- Removes tables for features no longer used by the application.

DROP TABLE IF EXISTS product_categories CASCADE;
DROP TABLE IF EXISTS screens CASCADE;
