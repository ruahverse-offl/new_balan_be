-- Order fulfillment lifecycle: staff queue, delivery assignment, cancel/return metadata.
-- Run against PostgreSQL after deploying model changes.

ALTER TABLE "T_orders"
    ADD COLUMN IF NOT EXISTS delivery_assigned_user_id UUID REFERENCES "M_users"(id),
    ADD COLUMN IF NOT EXISTS cancellation_reason TEXT,
    ADD COLUMN IF NOT EXISTS cancelled_by_user_id UUID REFERENCES "M_users"(id),
    ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS return_reason TEXT;

CREATE INDEX IF NOT EXISTS ix_t_orders_delivery_assigned_user_id
    ON "T_orders"(delivery_assigned_user_id)
    WHERE delivery_assigned_user_id IS NOT NULL AND is_deleted = false;

-- Align legacy statuses with canonical lifecycle values
UPDATE "T_orders" SET order_status = 'ORDER_RECEIVED' WHERE order_status = 'CONFIRMED';
UPDATE "T_orders" SET order_status = 'CANCELLED_BY_STAFF' WHERE order_status = 'CANCELLED';
UPDATE "T_orders" SET order_status = 'DELIVERED' WHERE order_status = 'COMPLETED';
UPDATE "T_orders" SET order_status = 'ORDER_PROCESSING' WHERE order_status = 'PROCESSING';
UPDATE "T_orders" SET order_status = 'OUT_FOR_DELIVERY' WHERE order_status = 'SHIPPED';
