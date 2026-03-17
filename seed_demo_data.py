"""
Seed script to add demo data for customer-facing pages.
Run from backend directory (with venv activated): python seed_demo_data.py

Production: Run migrations first (app startup does this), then seed_rbac_data.py
(if fresh DB), then this script. Medicines and brands are seeded with is_available=true.
"""
import asyncio
from sqlalchemy import text
from app.db.db_connection import DatabaseConnection


async def seed():
    DatabaseConnection.initialize()
    factory = DatabaseConnection.get_session_factory()

    async with factory() as session:
        # Get admin user ID for created_by
        r = await session.execute(text("SELECT id FROM users WHERE email='admin@newbalan.com'"))
        admin = r.fetchone()
        admin_id = str(admin.id)

        # Get customer user ID
        r = await session.execute(text("SELECT id FROM users WHERE email='customer@newbalan.com'"))
        customer = r.fetchone()
        customer_id = str(customer.id)

        print(f"Admin ID: {admin_id}")
        print(f"Customer ID: {customer_id}")

        # ========= 1. Fix 'Test' doctor =========
        await session.execute(text("""
            UPDATE doctors SET
                name = 'Dr. Kavitha Subramaniam',
                specialty = 'ENT Specialist',
                qualifications = 'MBBS, MS (ENT)',
                morning_timings = '10:00 AM - 1:00 PM',
                evening_timings = '5:00 PM - 8:00 PM',
                consultation_fee = 400
            WHERE name = 'Test'
        """))
        print("Updated Test doctor -> Dr. Kavitha Subramaniam (ENT)")

        # ========= 2. Add more doctors =========
        new_doctors = [
            ("Dr. Anand Krishnamurthy", "Dermatologist", "MBBS, MD (Dermatology)", "9:30 AM - 12:30 PM", "4:30 PM - 7:30 PM", 500),
            ("Dr. Lakshmi Narayanan", "Gynecologist", "MBBS, MS (OBG), DGO", "10:00 AM - 1:00 PM", "5:00 PM - 8:00 PM", 600),
            ("Dr. Suresh Kumar", "Orthopedic Surgeon", "MBBS, MS (Ortho), DNB", "9:00 AM - 12:00 PM", "4:00 PM - 7:00 PM", 550),
            ("Dr. Meena Raghavan", "Ophthalmologist", "MBBS, MS (Ophthalmology)", "10:30 AM - 1:30 PM", "5:30 PM - 8:00 PM", 450),
            ("Dr. Vijay Shankar", "Neurologist", "MBBS, MD (Neurology), DM", "9:00 AM - 12:00 PM", "4:00 PM - 6:30 PM", 700),
            ("Dr. Deepa Venkatesh", "Dentist", "BDS, MDS (Orthodontics)", "10:00 AM - 1:00 PM", "5:00 PM - 8:00 PM", 350),
        ]

        for name, spec, qual, morning, evening, fee in new_doctors:
            r = await session.execute(text("SELECT COUNT(*) FROM doctors WHERE name = :n"), {"n": name})
            if r.scalar() == 0:
                await session.execute(text("""
                    INSERT INTO doctors (name, specialty, qualifications, morning_timings, evening_timings, consultation_fee,
                        is_active, is_deleted, created_by, created_ip)
                    VALUES (:name, :spec, :qual, :morning, :evening, :fee,
                        true, false, :admin_id, '127.0.0.1')
                """), {
                    "name": name, "spec": spec, "qual": qual,
                    "morning": morning, "evening": evening, "fee": fee,
                    "admin_id": admin_id,
                })
                print(f"  Added doctor: {name} ({spec})")
            else:
                print(f"  Skip (exists): {name}")

        # ========= 3. Add more polyclinic tests =========
        new_tests = [
            ("Complete Blood Count (CBC)", "Comprehensive blood cell analysis including RBC, WBC, Hemoglobin, Platelets", 500, "30 minutes", False, "Droplets"),
            ("Thyroid Profile", "T3, T4, TSH levels to assess thyroid function", 650, "45 minutes", True, "Activity"),
            ("Liver Function Test", "SGOT, SGPT, Bilirubin, Albumin levels", 550, "30 minutes", True, "FlaskConical"),
            ("Kidney Function Test", "Creatinine, BUN, Uric Acid levels", 500, "30 minutes", True, "Beaker"),
            ("Lipid Profile", "Total Cholesterol, HDL, LDL, Triglycerides", 600, "45 minutes", True, "BarChart3"),
            ("Urine Analysis", "Complete urine examination for infections and abnormalities", 200, "20 minutes", False, "TestTube"),
            ("HbA1c", "Glycated hemoglobin test for 3-month diabetes control", 450, "30 minutes", False, "Gauge"),
            ("Vitamin D Test", "Measure Vitamin D levels in blood", 800, "30 minutes", False, "Sun"),
            ("CT Scan", "Computed Tomography scan for detailed internal imaging", 3500, "1 hour", True, "ScanLine"),
            ("MRI Scan", "Magnetic Resonance Imaging for soft tissue analysis", 5000, "1.5 hours", False, "Brain"),
        ]

        for name, desc, price, duration, fasting, icon in new_tests:
            r = await session.execute(text("SELECT COUNT(*) FROM polyclinic_tests WHERE name = :n"), {"n": name})
            if r.scalar() == 0:
                await session.execute(text("""
                    INSERT INTO polyclinic_tests (name, description, price, duration, fasting_required, icon_name,
                        is_active, is_deleted, created_by, created_ip)
                    VALUES (:name, :desc, :price, :duration, :fasting, :icon,
                        true, false, :admin_id, '127.0.0.1')
                """), {
                    "name": name, "desc": desc, "price": price, "duration": duration,
                    "fasting": fasting, "icon": icon, "admin_id": admin_id,
                })
                print(f"  Added test: {name} (Rs.{price})")
            else:
                print(f"  Skip (exists): {name}")

        # ========= 4. Add sample prescriptions =========
        r = await session.execute(text("SELECT COUNT(*) FROM prescriptions"))
        if r.scalar() == 0:
            # Prescription 1: Pending
            await session.execute(text("""
                INSERT INTO prescriptions (customer_id, file_url, file_name, file_size, file_type, status,
                    is_deleted, created_by, created_ip)
                VALUES (:cid, '/storage/prescriptions/prescription_sample1.jpg', 'prescription_sample1.jpg',
                    245000, 'image/jpeg', 'PENDING', false, :cid, '127.0.0.1')
            """), {"cid": customer_id})
            print("  Added prescription: prescription_sample1.jpg (PENDING)")

            # Prescription 2: Approved
            await session.execute(text("""
                INSERT INTO prescriptions (customer_id, file_url, file_name, file_size, file_type, status,
                    reviewed_by, review_notes, is_deleted, created_by, created_ip)
                VALUES (:cid, '/storage/prescriptions/prescription_dr_kumar.pdf', 'prescription_dr_kumar.pdf',
                    312000, 'application/pdf', 'APPROVED', :admin, 'Prescription verified and approved',
                    false, :cid, '127.0.0.1')
            """), {"cid": customer_id, "admin": admin_id})
            print("  Added prescription: prescription_dr_kumar.pdf (APPROVED)")

            # Prescription 3: Rejected
            await session.execute(text("""
                INSERT INTO prescriptions (customer_id, file_url, file_name, file_size, file_type, status,
                    reviewed_by, rejection_reason, is_deleted, created_by, created_ip)
                VALUES (:cid, '/storage/prescriptions/blurry_photo.jpg', 'blurry_photo.jpg',
                    180000, 'image/jpeg', 'REJECTED', :admin, 'Image is too blurry to read',
                    false, :cid, '127.0.0.1')
            """), {"cid": customer_id, "admin": admin_id})
            print("  Added prescription: blurry_photo.jpg (REJECTED)")
        else:
            print("  Prescriptions already exist, skipping")

        # ========= 5. Add therapeutic categories, medicines, and brands =========
        r = await session.execute(text("SELECT COUNT(*) FROM therapeutic_categories WHERE is_deleted = false"))
        tc_count = r.scalar()
        if tc_count == 0:
            tc_data = [
                ("Analgesics & Antipyretics", "Pain relievers and fever reducers"),
                ("Antibiotics", "Anti-bacterial medicines"),
                ("Antidiabetics", "Medicines for diabetes management"),
                ("Cardiovascular", "Heart and blood pressure medicines"),
                ("Gastrointestinal", "Stomach and digestive medicines"),
                ("Vitamins & Supplements", "Nutritional supplements"),
                ("Antihistamines", "Allergy relief medicines"),
                ("Respiratory", "Medicines for cough and respiratory issues"),
            ]
            for tc_name, tc_desc in tc_data:
                await session.execute(text("""
                    INSERT INTO therapeutic_categories (name, description, is_active, is_deleted, created_by, created_ip)
                    VALUES (:name, :desc, true, false, :admin_id, '127.0.0.1')
                """), {"name": tc_name, "desc": tc_desc, "admin_id": admin_id})
                print(f"  Added category: {tc_name}")
        else:
            print(f"  Therapeutic categories already exist ({tc_count}), skipping")

        # Fetch category IDs
        r = await session.execute(text("SELECT id, name FROM therapeutic_categories WHERE is_deleted = false"))
        tc_map = {row.name: str(row.id) for row in r.fetchall()}

        r = await session.execute(text("SELECT COUNT(*) FROM medicines WHERE is_deleted = false"))
        med_count = r.scalar()
        if med_count == 0:
            medicines_data = [
                ("Paracetamol 500mg", "Tablet", "Analgesics & Antipyretics", False, False, "OTC", "Effective pain reliever and fever reducer for headache, body pain, and common cold"),
                ("Amoxicillin 500mg", "Capsule", "Antibiotics", True, False, "H1", "Broad-spectrum antibiotic for bacterial infections"),
                ("Metformin 500mg", "Tablet", "Antidiabetics", True, False, "H1", "First-line treatment for Type 2 diabetes to control blood sugar"),
                ("Amlodipine 5mg", "Tablet", "Cardiovascular", True, False, "H1", "Calcium channel blocker for high blood pressure and chest pain"),
                ("Pantoprazole 40mg", "Tablet", "Gastrointestinal", True, False, "H1", "Proton pump inhibitor for acidity, GERD, and stomach ulcers"),
                ("Cetirizine 10mg", "Tablet", "Antihistamines", False, False, "OTC", "Antihistamine for allergies, sneezing, runny nose, and hives"),
                ("Azithromycin 500mg", "Tablet", "Antibiotics", True, False, "H1", "Macrolide antibiotic for respiratory and skin infections"),
                ("Vitamin D3 60000 IU", "Softgel", "Vitamins & Supplements", False, False, "OTC", "High-dose Vitamin D supplement for deficiency"),
                ("Dolo 650", "Tablet", "Analgesics & Antipyretics", False, False, "OTC", "Paracetamol 650mg for fever and moderate pain relief"),
                ("Omeprazole 20mg", "Capsule", "Gastrointestinal", True, False, "H1", "Acid reducer for heartburn and stomach ulcers"),
                ("Montelukast 10mg", "Tablet", "Respiratory", True, False, "H1", "Leukotriene receptor antagonist for asthma and allergies"),
                ("Calcium + Vitamin D3", "Tablet", "Vitamins & Supplements", False, False, "OTC", "Calcium 500mg with Vitamin D3 for bone health"),
                ("Ibuprofen 400mg", "Tablet", "Analgesics & Antipyretics", False, False, "OTC", "NSAID for pain, inflammation, and fever"),
                ("Atorvastatin 10mg", "Tablet", "Cardiovascular", True, False, "H1", "Statin for lowering cholesterol and preventing heart disease"),
                ("Multivitamin Complex", "Tablet", "Vitamins & Supplements", False, False, "OTC", "Daily multivitamin with essential minerals for overall health"),
            ]

            for m_name, dosage, cat_name, rx, ctrl, sched, desc in medicines_data:
                tc_id = tc_map.get(cat_name)
                if not tc_id:
                    continue
                await session.execute(text("""
                    INSERT INTO medicines (name, dosage_form, therapeutic_category_id, is_prescription_required, is_controlled,
                        schedule_type, description, is_active, is_available, is_deleted, created_by, created_ip)
                    VALUES (:name, :dosage, :tc_id, :rx, :ctrl, :sched, :desc,
                        true, true, false, :admin_id, '127.0.0.1')
                """), {
                    "name": m_name, "dosage": dosage, "tc_id": tc_id,
                    "rx": rx, "ctrl": ctrl, "sched": sched, "desc": desc,
                    "admin_id": admin_id,
                })
                print(f"  Added medicine: {m_name}")
        else:
            print(f"  Medicines already exist ({med_count}), skipping")

        # Fetch medicine IDs
        r = await session.execute(text("SELECT id, name FROM medicines WHERE is_deleted = false"))
        med_map = {row.name: str(row.id) for row in r.fetchall()}

        r = await session.execute(text("SELECT COUNT(*) FROM medicine_brands WHERE is_deleted = false"))
        brand_count = r.scalar()
        if brand_count == 0:
            brands_data = [
                ("Paracetamol 500mg", "Crocin Advance", "GSK Consumer Healthcare", 25.00),
                ("Paracetamol 500mg", "Dolo 500", "Micro Labs", 22.00),
                ("Amoxicillin 500mg", "Mox 500", "Aristo Pharmaceuticals", 85.50),
                ("Amoxicillin 500mg", "Novamox 500", "Cipla", 92.00),
                ("Metformin 500mg", "Glycomet 500", "USV Pvt Ltd", 32.00),
                ("Metformin 500mg", "Glucophage 500", "Franco-Indian", 45.00),
                ("Amlodipine 5mg", "Amlong 5", "Micro Labs", 28.00),
                ("Amlodipine 5mg", "Stamlo 5", "Dr. Reddy's", 35.50),
                ("Pantoprazole 40mg", "Pan 40", "Alkem Laboratories", 55.00),
                ("Pantoprazole 40mg", "Pantocid 40", "Sun Pharma", 62.00),
                ("Cetirizine 10mg", "Cetzine", "Dr. Reddy's", 18.00),
                ("Cetirizine 10mg", "Okacet", "Cipla", 15.00),
                ("Azithromycin 500mg", "Azithral 500", "Alembic Pharma", 95.00),
                ("Azithromycin 500mg", "Zithromax 500", "Pfizer", 120.00),
                ("Vitamin D3 60000 IU", "D-Rise 60K", "USV Pvt Ltd", 115.00),
                ("Vitamin D3 60000 IU", "Tayo 60K", "Eris Lifesciences", 130.00),
                ("Dolo 650", "Dolo 650", "Micro Labs", 30.00),
                ("Omeprazole 20mg", "Omez 20", "Dr. Reddy's", 40.00),
                ("Omeprazole 20mg", "Ocid 20", "Zydus Cadila", 38.00),
                ("Montelukast 10mg", "Montair 10", "Cipla", 145.00),
                ("Montelukast 10mg", "Singulair 10", "MSD", 180.00),
                ("Calcium + Vitamin D3", "Shelcal 500", "Torrent Pharma", 125.00),
                ("Calcium + Vitamin D3", "Gemcal", "Ipca Labs", 110.00),
                ("Ibuprofen 400mg", "Brufen 400", "Abbott India", 20.00),
                ("Ibuprofen 400mg", "Ibugesic 400", "Cipla", 18.50),
                ("Atorvastatin 10mg", "Atorva 10", "Zydus Cadila", 65.00),
                ("Atorvastatin 10mg", "Lipitor 10", "Pfizer", 85.00),
                ("Multivitamin Complex", "Supradyn", "Bayer", 95.00),
                ("Multivitamin Complex", "Becosules Z", "Pfizer", 45.00),
            ]

            for med_name, brand_name, manufacturer, mrp in brands_data:
                mid = med_map.get(med_name)
                if not mid:
                    continue
                await session.execute(text("""
                    INSERT INTO medicine_brands (medicine_id, brand_name, manufacturer, mrp,
                        is_active, is_available, is_deleted, created_by, created_ip)
                    VALUES (:mid, :brand, :mfg, :mrp,
                        true, true, false, :admin_id, '127.0.0.1')
                """), {
                    "mid": mid, "brand": brand_name, "mfg": manufacturer, "mrp": mrp,
                    "admin_id": admin_id,
                })
                print(f"  Added brand: {brand_name} ({manufacturer}) - Rs.{mrp}")
        else:
            print(f"  Medicine brands already exist ({brand_count}), skipping")

        # ========= 6. Update existing doctor descriptions =========
        updates = [
            ("Dr. M. Sridharan", "MBBS, MD (General Medicine)", "9:00 AM - 12:00 PM", "4:00 PM - 7:00 PM", 300),
            ("Dr. Priya Menon", "MBBS, MD (Cardiology), DM", "10:00 AM - 1:00 PM", "5:00 PM - 7:30 PM", 800),
            ("Dr. Ramesh Iyer", "MBBS, MD (Pediatrics), DCH", "9:30 AM - 12:30 PM", "4:30 PM - 7:00 PM", 400),
        ]
        for name, qual, morning, evening, fee in updates:
            r = await session.execute(text("SELECT qualifications FROM doctors WHERE name = :n"), {"n": name})
            row = r.fetchone()
            if row and not row.qualifications:
                await session.execute(text("""
                    UPDATE doctors SET qualifications = :qual, morning_timings = :morning,
                        evening_timings = :evening, consultation_fee = :fee
                    WHERE name = :name
                """), {"name": name, "qual": qual, "morning": morning, "evening": evening, "fee": fee})
                print(f"  Updated doctor qualifications: {name}")

        # ========= 6. Update polyclinic test descriptions =========
        test_updates = {
            "Blood Test": ("Complete blood panel including CBC, sugar levels, and basic metabolic panel", "30 minutes", False, "Droplets"),
            "Diabetes Test": ("Fasting blood sugar and HbA1c to monitor diabetes", "45 minutes", True, "Activity"),
            "ECG": ("12-lead electrocardiogram for heart rhythm analysis", "15 minutes", False, "HeartPulse"),
            "X-Ray": ("Digital X-ray imaging for bone and chest examination", "20 minutes", False, "Bone"),
            "Ultrasound": ("Abdominal ultrasound for internal organ examination", "30 minutes", True, "Waves"),
        }
        for name, (desc, dur, fasting, icon) in test_updates.items():
            r = await session.execute(text("SELECT description FROM polyclinic_tests WHERE name = :n"), {"n": name})
            row = r.fetchone()
            if row and (not row.description or len(row.description) < 20):
                await session.execute(text("""
                    UPDATE polyclinic_tests SET description = :desc, duration = :dur,
                        fasting_required = :fasting, icon_name = :icon
                    WHERE name = :name
                """), {"name": name, "desc": desc, "dur": dur, "fasting": fasting, "icon": icon})
                print(f"  Updated test details: {name}")

        # ========= 7. Coupons (required for coupon usages) =========
        r = await session.execute(text("SELECT COUNT(*) FROM coupons WHERE is_deleted = false"))
        coupon_count = r.scalar()
        if coupon_count == 0:
            coupon_data = [
                ("SAVE10", 10.00, 500.00, 100.00, 100),
                ("WELCOME20", 20.00, 300.00, 75.00, 50),
                ("FLAT50", 15.00, 1000.00, 150.00, 200),
            ]
            for code, pct, min_ord, max_disc, limit in coupon_data:
                await session.execute(text("""
                    INSERT INTO coupons (code, discount_percentage, min_order_amount, max_discount_amount, usage_limit, usage_count,
                        is_active, is_deleted, created_by, created_ip)
                    VALUES (:code, :pct, :min_ord, :max_disc, :limit, 0,
                        true, false, :admin_id, '127.0.0.1')
                """), {"code": code, "pct": pct, "min_ord": min_ord, "max_disc": max_disc, "limit": limit, "admin_id": admin_id})
                print(f"  Added coupon: {code} ({pct}% off)")
        else:
            print(f"  Coupons already exist ({coupon_count}), skipping")

        # ========= 8. Sample orders (required for coupon usages) =========
        r = await session.execute(text("SELECT COUNT(*) FROM orders WHERE is_deleted = false"))
        order_count = r.scalar()
        if order_count == 0:
            orders_data = [
                ("Ramesh Kumar", "9876543210", "123 MG Road, Bangalore", "website", "DELIVERED", "APPROVED", 850.00, 85.00, 50.00, 815.00, "online", customer_id),
                ("Priya Sharma", "8765432109", "45 Park Street, Kolkata", "store", "CONFIRMED", "APPROVED", 420.00, 42.00, 40.00, 418.00, "cash", customer_id),
                ("Vikram Singh", "7654321098", "78 Anna Nagar, Chennai", "website", "PENDING", "PENDING", 1200.00, 120.00, 60.00, 1140.00, "online", None),
            ]
            for cname, phone, addr, src, ostatus, astatus, total, disc, delfee, final, pay, cid in orders_data:
                await session.execute(text("""
                    INSERT INTO orders (customer_name, customer_phone, delivery_address, order_source, order_status, approval_status,
                        total_amount, discount_amount, delivery_fee, final_amount, payment_method, customer_id,
                        is_deleted, created_by, created_ip)
                    VALUES (:cname, :phone, :addr, :src, :ostatus, :astatus,
                        :total, :disc, :delfee, :final, :pay, :cid,
                        false, :admin_id, '127.0.0.1')
                """), {
                    "cname": cname, "phone": phone, "addr": addr, "src": src, "ostatus": ostatus, "astatus": astatus,
                    "total": total, "disc": disc, "delfee": delfee, "final": final, "pay": pay, "cid": cid, "admin_id": admin_id,
                })
                print(f"  Added order: {cname} - Rs.{final}")
        else:
            print(f"  Orders already exist ({order_count}), skipping")

        # ========= 9. Dummy coupon + order + coupon_usage (all fields saved in DB for Coupon Usages tab) =========
        r = await session.execute(text("SELECT id FROM coupons WHERE code = 'DEMO20' AND is_deleted = false"))
        demo_coupon_row = r.fetchone()
        if demo_coupon_row is None:
            await session.execute(text("""
                INSERT INTO coupons (code, discount_percentage, min_order_amount, max_discount_amount, usage_limit, usage_count,
                    is_active, is_deleted, created_by, created_ip)
                VALUES ('DEMO20', 20.00, 200.00, 100.00, 999, 0,
                    true, false, :admin_id, '127.0.0.1')
            """), {"admin_id": admin_id})
            r = await session.execute(text("SELECT id FROM coupons WHERE code = 'DEMO20' AND is_deleted = false"))
            demo_coupon_row = r.fetchone()
            print("  Added dummy coupon: DEMO20 (20% off, min order Rs.200)")
        demo_coupon_id = str(demo_coupon_row.id)

        r = await session.execute(text("SELECT id FROM orders WHERE customer_name = 'Demo Customer' AND customer_phone = '9999888877' AND is_deleted = false"))
        demo_order_row = r.fetchone()
        if demo_order_row is None:
            await session.execute(text("""
                INSERT INTO orders (customer_name, customer_phone, delivery_address, order_source, order_status, approval_status,
                    total_amount, discount_amount, delivery_fee, final_amount, payment_method, customer_id,
                    is_deleted, created_by, created_ip)
                VALUES ('Demo Customer', '9999888877', '123 Demo Street, Demo City', 'website', 'DELIVERED', 'APPROVED',
                    1500.00, 100.00, 50.00, 1450.00, 'online', :cid,
                    false, :admin_id, '127.0.0.1')
            """), {"cid": customer_id, "admin_id": admin_id})
            r = await session.execute(text("SELECT id FROM orders WHERE customer_name = 'Demo Customer' AND customer_phone = '9999888877' AND is_deleted = false"))
            demo_order_row = r.fetchone()
            print("  Added dummy order: Demo Customer, Rs.1450 final (discount Rs.100)")
        demo_order_id = str(demo_order_row.id)

        r = await session.execute(text("""
            SELECT 1 FROM coupon_usages cu
            JOIN coupons c ON c.id = cu.coupon_id AND c.code = 'DEMO20' AND c.is_deleted = false
            JOIN orders o ON o.id = cu.order_id AND o.customer_name = 'Demo Customer' AND o.is_deleted = false
            WHERE cu.is_deleted = false
        """))
        if r.fetchone() is None:
            await session.execute(text("""
                INSERT INTO coupon_usages (coupon_id, order_id, customer_id, discount_amount,
                    coupon_code, customer_name, customer_phone, order_final_amount,
                    is_deleted, created_by, created_ip)
                VALUES (:cid, :oid, :cust_id, 100.00,
                    'DEMO20', 'Demo Customer', '9999888877', 1450.00,
                    false, :admin_id, '127.0.0.1')
            """), {"cid": demo_coupon_id, "oid": demo_order_id, "cust_id": customer_id, "admin_id": admin_id})
            await session.execute(text("UPDATE coupons SET usage_count = usage_count + 1 WHERE id = :id"), {"id": demo_coupon_id})
            print("  Added dummy coupon usage: DEMO20 -> Demo Customer, discount Rs.100, order total Rs.1450 (all saved in DB).")

        # ========= 10. Extra coupon usages (if none exist besides dummy) =========
        r = await session.execute(text("SELECT id FROM coupons WHERE is_deleted = false AND code != 'DEMO20' ORDER BY code LIMIT 3"))
        coupon_rows = r.fetchall()
        r = await session.execute(text("SELECT id FROM orders WHERE is_deleted = false AND (customer_name != 'Demo Customer' OR customer_phone != '9999888877') ORDER BY created_at DESC LIMIT 5"))
        order_rows = r.fetchall()
        r = await session.execute(text("SELECT COUNT(*) FROM coupon_usages WHERE is_deleted = false"))
        usage_count = r.scalar()
        if usage_count <= 1 and coupon_rows and order_rows:
            coupon_ids = [str(row.id) for row in coupon_rows]
            order_ids = [str(row.id) for row in order_rows]
            dummy_discounts = [85.00, 42.00, 120.00]
            for i in range(min(3, len(coupon_ids), len(order_ids))):
                cid = coupon_ids[i]
                oid = order_ids[i]
                disc_amt = dummy_discounts[i] if i < len(dummy_discounts) else 50.00
                r_ord = await session.execute(text(
                    "SELECT customer_name, customer_phone, final_amount FROM orders WHERE id = :oid"
                ), {"oid": order_ids[i]})
                row_ord = r_ord.fetchone()
                cname = row_ord.customer_name or "Customer" if row_ord else "Customer"
                cphone = row_ord.customer_phone or "—" if row_ord else "—"
                ofinal = float(row_ord.final_amount) if row_ord and row_ord.final_amount else 0
                r_cp = await session.execute(text("SELECT code FROM coupons WHERE id = :cid"), {"cid": cid})
                row_cp = r_cp.fetchone()
                cp_code = row_cp.code if row_cp else "—"
                await session.execute(text("""
                    INSERT INTO coupon_usages (coupon_id, order_id, customer_id, discount_amount,
                        coupon_code, customer_name, customer_phone, order_final_amount,
                        is_deleted, created_by, created_ip)
                    VALUES (:cid, :oid, :cust_id, :disc,
                        :cp_code, :cname, :cphone, :ofinal,
                        false, :admin_id, '127.0.0.1')
                """), {"cid": cid, "oid": oid, "cust_id": customer_id, "disc": disc_amt,
                       "cp_code": cp_code, "cname": cname, "cphone": cphone, "ofinal": ofinal, "admin_id": admin_id})
                print(f"  Added coupon usage: discount Rs.{disc_amt}")
            for cid in coupon_ids[:3]:
                await session.execute(text("UPDATE coupons SET usage_count = usage_count + 1 WHERE id = :id"), {"id": cid})
            print("  Extra coupon usages seeded (3 more records).")

        # ========= 11. Backfill orders referenced by coupon_usages (so Coupon Usages tab shows customer, phone, order total) =========
        r = await session.execute(text("""
            UPDATE orders o SET customer_name = COALESCE(NULLIF(TRIM(o.customer_name), ''), 'Customer')
            WHERE o.id IN (SELECT order_id FROM coupon_usages WHERE is_deleted = false)
            AND (o.customer_name IS NULL OR TRIM(o.customer_name) = '')
            RETURNING o.id
        """))
        updated = r.fetchall()
        if updated:
            print(f"  Backfilled customer_name for {len(updated)} order(s) linked to coupon usages.")

        await session.commit()
        print("\nAll demo data seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
