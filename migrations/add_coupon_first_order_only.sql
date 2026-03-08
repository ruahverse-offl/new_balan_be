-- Add first_order_only to coupons (for "first order only" coupon type)
-- Run once: psql -U your_user -d your_db -f add_coupon_first_order_only.sql
ALTER TABLE coupons
ADD COLUMN IF NOT EXISTS first_order_only BOOLEAN NOT NULL DEFAULT false;
