-- Insert DELIVERY_ASSIGNED notification template into M_notification_master
-- Run this script in your PostgreSQL database

-- First, check if the template already exists
DO $$
DECLARE
    template_exists BOOLEAN;
    admin_user_id UUID;
BEGIN
    -- Check if template exists
    SELECT EXISTS (
        SELECT 1 FROM "M_notification_master"
        WHERE event_code = 'DELIVERY_ASSIGNED' AND is_deleted = false
    ) INTO template_exists;

    IF template_exists THEN
        RAISE NOTICE 'DELIVERY_ASSIGNED notification template already exists. Skipping insert.';
    ELSE
        -- Get the first admin user ID for audit fields
        SELECT id INTO admin_user_id
        FROM "M_users"
        WHERE is_deleted = false
        LIMIT 1;

        -- Insert the notification template
        INSERT INTO "M_notification_master" (
            id,
            event_code,
            event_name,
            description,
            channel_templates,
            is_active,
            is_deleted,
            created_at,
            updated_at,
            created_by,
            updated_by,
            created_ip,
            updated_ip
        ) VALUES (
            gen_random_uuid(),
            'DELIVERY_ASSIGNED',
            'Delivery assigned',
            'Fired when staff assigns or reassigns a delivery agent to an order',
            '{"push": {"title_template": "New delivery assigned", "body_template": "Order {{order_reference}} for {{customer_name}}. Open the app to view.", "message_variables": ["order_reference", "customer_name", "order_status", "delivery_address"], "is_enabled": true}}',
            true,
            false,
            NOW(),
            NOW(),
            COALESCE(admin_user_id, gen_random_uuid()),
            COALESCE(admin_user_id, gen_random_uuid()),
            '127.0.0.1',
            '127.0.0.1'
        );

        RAISE NOTICE 'DELIVERY_ASSIGNED notification template inserted successfully!';
    END IF;
END $$;

-- Verify the insert
SELECT
    id,
    event_code,
    event_name,
    description,
    channel_templates,
    is_active,
    created_at
FROM "M_notification_master"
WHERE event_code = 'DELIVERY_ASSIGNED' AND is_deleted = false;
