"""
Ensure every coupon_usage has a valid order (backfill missing orders) and optionally seed
demo orders with coupon usages so the Coupon Usages tab has data to show.
Run from backend dir: python seed_coupon_usages_orders.py
Optional: python seed_coupon_usages_orders.py --add-demo  (adds 2 more demo orders with coupon usages)
"""
import asyncio
import sys
from sqlalchemy import text
from app.db.db_connection import DatabaseConnection


async def run(add_demo=False):
    DatabaseConnection.initialize()
    factory = DatabaseConnection.get_session_factory()

    async with factory() as session:
        # Get an admin/user id for created_by
        r = await session.execute(text("SELECT id FROM users WHERE is_deleted = false LIMIT 1"))
        user_row = r.fetchone()
        admin_id = str(user_row.id) if user_row else None
        if not admin_id:
            print("No user found. Create a user first (e.g. run seed or register).")
            return

        # ---------- 1. Backfill: for each coupon_usage whose order is missing, create order and fix reference ----------
        r = await session.execute(text("""
            SELECT cu.id AS usage_id, cu.order_id, cu.coupon_id, cu.discount_amount,
                   cu.coupon_code, cu.customer_name, cu.customer_phone, cu.order_final_amount,
                   cu.created_by, cu.created_ip
            FROM coupon_usages cu
            LEFT JOIN orders o ON o.id = cu.order_id AND o.is_deleted = false
            WHERE cu.is_deleted = false AND o.id IS NULL
        """))
        usages_missing_order = r.fetchall()

        for row in usages_missing_order:
            usage_id = str(row.usage_id)
            old_order_id = str(row.order_id)
            discount = float(row.discount_amount or 0)
            final = float(row.order_final_amount or 0)
            total = final + discount
            cname = (row.customer_name or "").strip() or "Customer"
            cphone = (row.customer_phone or "").strip() or "9999999999"
            created_by = str(row.created_by) if row.created_by else admin_id
            created_ip = row.created_ip or "127.0.0.1"

            await session.execute(text("""
                INSERT INTO orders (customer_name, customer_phone, delivery_address, order_source, order_status, approval_status,
                    total_amount, discount_amount, delivery_fee, final_amount, payment_method, customer_id,
                    is_deleted, created_by, created_ip)
                VALUES (:cname, :phone, 'Address from coupon usage', 'website', 'CONFIRMED', 'APPROVED',
                    :total, :disc, 0, :final, 'online', NULL,
                    false, :created_by::uuid, :created_ip)
            """), {"cname": cname, "phone": cphone, "total": total, "disc": discount, "final": final, "created_by": created_by, "created_ip": created_ip})

            r2 = await session.execute(text("SELECT id FROM orders WHERE customer_phone = :phone AND total_amount = :total AND discount_amount = :disc ORDER BY created_at DESC LIMIT 1"), {"phone": cphone, "total": total, "disc": discount})
            new_order_row = r2.fetchone()
            if new_order_row:
                new_order_id = str(new_order_row.id)
                await session.execute(text("UPDATE coupon_usages SET order_id = :oid WHERE id = :uid"), {"oid": new_order_id, "uid": usage_id})
                print(f"  Backfilled order for coupon usage {usage_id[:8]}... -> order {new_order_id[:8]}... ({cname}, Rs.{final})")

        if usages_missing_order:
            print(f"Backfilled {len(usages_missing_order)} order(s) for coupon usages that had missing orders.")

        # ---------- 2. Seed demo orders with coupon usages if none exist ----------
        r = await session.execute(text("SELECT COUNT(*) FROM coupon_usages WHERE is_deleted = false"))
        usage_count = r.scalar()
        if usage_count > 0 and not add_demo:
            print(f"Coupon usages already exist ({usage_count}). Skipping demo seed. Use --add-demo to add more.")
            await session.commit()
            return

        # Get a customer id and coupons
        r = await session.execute(text("SELECT id FROM users WHERE is_deleted = false AND email LIKE '%customer%' LIMIT 1"))
        cust = r.fetchone()
        customer_id = str(cust.id) if cust else None
        r = await session.execute(text("SELECT id, code FROM coupons WHERE is_deleted = false AND is_active = true ORDER BY code LIMIT 5"))
        coupons = r.fetchall()
        if not coupons:
            await session.execute(text("""
                INSERT INTO coupons (code, discount_percentage, min_order_amount, max_discount_amount, usage_limit, usage_count,
                    is_active, is_deleted, created_by, created_ip)
                VALUES ('DEMO20', 20, 200, 100, 999, 0, true, false, :aid, '127.0.0.1')
            """), {"aid": admin_id})
            r = await session.execute(text("SELECT id, code FROM coupons WHERE code = 'DEMO20' AND is_deleted = false"))
            coupons = r.fetchall()

        # Create demo orders with discount and link coupon_usages (3 if no usages yet, 2 if --add-demo)
        extra = [
            ("Extra Order A", "9111111111", "100 Seed Lane, City", 1200.00, 80.00, 50.00, 1170.00),
            ("Extra Order B", "9222222222", "200 Seed Ave, Town", 700.00, 50.00, 40.00, 690.00),
        ] if add_demo else []
        demo_orders = [
            ("Demo Customer", "9999888877", "123 Demo St, Demo City", 1500.00, 100.00, 50.00, 1450.00),
            ("Ramesh Kumar", "9876543210", "456 MG Road, Bangalore", 850.00, 85.00, 40.00, 805.00),
            ("Priya Sharma", "8765432109", "78 Park St, Kolkata", 600.00, 60.00, 40.00, 580.00),
        ] + extra
        coupon_id = str(coupons[0].id)
        coupon_code = coupons[0].code or "DEMO20"

        for cname, phone, addr, total, disc, delfee, final in demo_orders:
            await session.execute(text("""
                INSERT INTO orders (customer_name, customer_phone, delivery_address, order_source, order_status, approval_status,
                    total_amount, discount_amount, delivery_fee, final_amount, payment_method, customer_id,
                    is_deleted, created_by, created_ip)
                VALUES (:cname, :phone, :addr, 'website', 'DELIVERED', 'APPROVED',
                    :total, :disc, :delfee, :final, 'online', :cid,
                    false, :aid, '127.0.0.1')
            """), {"cname": cname, "phone": phone, "addr": addr, "total": total, "disc": disc, "delfee": delfee, "final": final, "cid": customer_id, "aid": admin_id})

            r = await session.execute(text("SELECT id FROM orders WHERE customer_phone = :phone AND final_amount = :final ORDER BY created_at DESC LIMIT 1"), {"phone": phone, "final": final})
            order_row = r.fetchone()
            if order_row:
                order_id = str(order_row.id)
                await session.execute(text("""
                    INSERT INTO coupon_usages (coupon_id, order_id, customer_id, discount_amount,
                        coupon_code, customer_name, customer_phone, order_final_amount,
                        is_deleted, created_by, created_ip)
                    VALUES (:cid, :oid, :cust_id, :disc, :code, :cname, :phone, :final,
                        false, :aid, '127.0.0.1')
                """), {"cid": coupon_id, "oid": order_id, "cust_id": customer_id, "disc": disc, "code": coupon_code, "cname": cname, "phone": phone, "final": final, "aid": admin_id})
                await session.execute(text("UPDATE coupons SET usage_count = usage_count + 1 WHERE id = :id"), {"id": coupon_id})
                print(f"  Created order + coupon usage: {cname}, Rs.{final} (discount Rs.{disc})")

        await session.commit()
        print("Done. Coupon usages now have valid orders; you can open order details from the Coupon Usages tab.")


if __name__ == "__main__":
    add_demo = "--add-demo" in sys.argv
    asyncio.run(run(add_demo=add_demo))
