# Master Data Setup Guide

## Overview

This document outlines all the **master data** (reference data) that clients need to provide **before** the system can be fully operational. Master data is the foundational information that doesn't change frequently and is required for day-to-day operations.

---

## Table of Contents

1. [Initial Setup Checklist](#initial-setup-checklist)
2. [Roles and Permissions](#1-roles-and-permissions)
3. [Therapeutic Categories](#2-therapeutic-categories)
4. [Medicine Catalog](#3-medicine-catalog)
5. [Medicine Images/Pictures](#4-medicine-imagespictures)
6. [User Accounts](#5-user-accounts)
7. [Master Data Import Template](#master-data-import-template)

---

## Initial Setup Checklist

Before starting operations, ensure you have collected:

- [ ] **Roles and Permissions** - Define user roles and their permissions
- [ ] **Therapeutic Categories** - Medicine categories (Antibiotic, Pain Reliever, etc.)
- [ ] **Medicine Catalog** - Complete medicine information with images
- [ ] **User Accounts** - Staff and pharmacist accounts
- [ ] **Initial Inventory** - Stock rows in `product_batches` (direct DB; no Product Batches admin API)

---

## 1. Roles and Permissions

### Master Data Required

#### A. Roles (User Types)

**Purpose:** Define what types of users exist in your pharmacy

**Data to Collect:**

| Role Name | Description | When to Use |
|-----------|------------|-------------|
| `PHARMACIST` | Licensed pharmacist who can review and approve prescriptions | For licensed pharmacists |
| `ADMIN` | System administrator with full access | For pharmacy owners/managers |
| `CASHIER` | Cashier who processes payments | For front desk staff |
| `MANAGER` | Store manager for inventory and operations | For store managers |
| `CUSTOMER_SERVICE` | Customer service representative | For customer support staff |
| `CUSTOMER` | End customer who places orders | For regular customers |

**Example Data:**
```json
[
  {
    "name": "PHARMACIST",
    "description": "Licensed pharmacist who can review and approve prescriptions"
  },
  {
    "name": "ADMIN",
    "description": "System administrator with full access to all features"
  },
  {
    "name": "CASHIER",
    "description": "Cashier who processes payments and handles transactions"
  },
  {
    "name": "MANAGER",
    "description": "Store manager who manages inventory and operations"
  }
]
```

#### B. Permissions (Actions)

**Purpose:** Define what actions can be performed in the system

**Data to Collect:**

| Permission Code | Description | Required For |
|----------------|-------------|--------------|
| `PRESCRIPTION_REVIEW` | Review and validate prescriptions | Pharmacists |
| `PRESCRIPTION_APPROVE` | Approve prescriptions for dispensing | Pharmacists |
| `INVENTORY_VIEW` | View inventory levels | All staff |
| `INVENTORY_UPDATE` | Update inventory quantities | Managers, Pharmacists |
| `ORDER_CREATE` | Create new orders | Cashiers, Staff |
| `ORDER_CANCEL` | Cancel existing orders | Managers, Pharmacists |
| `ORDER_APPROVE` | Approve orders | Pharmacists |
| `PAYMENT_PROCESS` | Process payments | Cashiers |
| `PAYMENT_REFUND` | Process refunds | Managers |
| `USER_MANAGE` | Manage user accounts | Admins |
| `REPORT_VIEW` | View reports and analytics | Managers, Admins |
| `DASHBOARD_VIEW` | View admin Statistics KPIs (`GET /api/v1/kpi/summary`) | Managers, Admins |

**Example Data:**
```json
[
  {
    "code": "PRESCRIPTION_REVIEW",
    "description": "Can review and validate prescriptions"
  },
  {
    "code": "PRESCRIPTION_APPROVE",
    "description": "Can approve prescriptions for dispensing"
  },
  {
    "code": "INVENTORY_VIEW",
    "description": "Can view inventory levels and stock information"
  },
  {
    "code": "INVENTORY_UPDATE",
    "description": "Can update inventory quantities (stock levels)"
  }
]
```

#### C. Role Permissions Mapping

**Purpose:** Assign permissions to roles

**Data to Collect:**

For each role, specify which permissions it should have:

**Example: PHARMACIST Role**
```json
{
  "role_id": "<PHARMACIST_ROLE_ID>",
  "permissions": [
    "PRESCRIPTION_REVIEW",
    "PRESCRIPTION_APPROVE",
    "INVENTORY_VIEW",
    "INVENTORY_UPDATE",
    "ORDER_APPROVE",
    "REPORT_VIEW",
    "DASHBOARD_VIEW"
  ]
}
```

**Example: CASHIER Role**
```json
{
  "role_id": "<CASHIER_ROLE_ID>",
  "permissions": [
    "INVENTORY_VIEW",
    "ORDER_CREATE",
    "PAYMENT_PROCESS"
  ]
}
```

---

## 2. Therapeutic Categories

### Master Data Required

**Purpose:** Classify medicines by their medical purpose

**Data to Collect:**

| Category Name | Description | Common Medicines |
|--------------|-------------|------------------|
| `Antibiotic` | Drugs used to treat bacterial infections | Amoxicillin, Azithromycin |
| `Pain Reliever` | For pain management | Paracetamol, Ibuprofen, Aspirin |
| `Antacid` | For treating acidity and indigestion | Omeprazole, Ranitidine |
| `Antihistamine` | For allergies and cold symptoms | Cetirizine, Loratadine |
| `Vitamin` | Nutritional supplements | Vitamin D, Vitamin B12, Multivitamin |
| `Cardiac` | Heart-related medicines | Atorvastatin, Metoprolol |
| `Diabetes` | Diabetes management | Metformin, Glimepiride |
| `Antifungal` | For fungal infections | Clotrimazole, Fluconazole |
| `Antiviral` | For viral infections | Acyclovir, Oseltamivir |
| `Cough & Cold` | For cough and cold symptoms | Dextromethorphan, Pseudoephedrine |
| `Dermatology` | Skin-related medicines | Hydrocortisone, Clobetasol |
| `Gastrointestinal` | Digestive system medicines | Domperidone, Pantoprazole |
| `Respiratory` | Breathing-related medicines | Salbutamol, Montelukast |
| `Neurological` | Nervous system medicines | Carbamazepine, Gabapentin |
| `Hormonal` | Hormone-related medicines | Levothyroxine, Prednisolone |

**Example Data:**
```json
[
  {
    "name": "Antibiotic",
    "description": "Drugs used to treat bacterial infections"
  },
  {
    "name": "Pain Reliever",
    "description": "Medicines for pain management and fever reduction"
  },
  {
    "name": "Antacid",
    "description": "Medicines for treating acidity, indigestion, and heartburn"
  },
  {
    "name": "Vitamin",
    "description": "Nutritional supplements and vitamins"
  }
]
```

---

## 3. Medicine Catalog

### Master Data Required

This is the **most important** master data. You need to set up your complete medicine catalog.

#### A. Medicines (Generic Medicine Information)

**Data to Collect for Each Medicine:**

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| `name` | ✅ Yes | Generic medicine name | `"Paracetamol"` |
| `dosage_form` | ✅ Yes | Form of medicine | `"Tablet"`, `"Capsule"`, `"Syrup"`, `"Injection"`, `"Ointment"`, `"Drops"` |
| `therapeutic_category_id` | ✅ Yes | Category UUID | Get from therapeutic categories |
| `is_prescription_required` | ✅ Yes | Requires prescription? | `true` or `false` |
| `is_controlled` | ✅ Yes | Controlled substance? | `true` or `false` |
| `schedule_type` | ✅ Yes | Regulatory schedule | `"OTC"`, `"Schedule H"`, `"Schedule H1"`, `"Schedule X"` |
| `description` | ❌ No | Medicine description | `"Pain reliever and fever reducer"` |

**Dosage Forms:**
- `Tablet` - Solid oral form
- `Capsule` - Gelatin-coated form
- `Syrup` - Liquid oral form
- `Injection` - Injectable form
- `Ointment` - Topical application
- `Drops` - Liquid drops (eye/ear/nose)
- `Cream` - Topical cream
- `Gel` - Topical gel
- `Spray` - Nasal/spray form
- `Inhaler` - Inhalation device

**Schedule Types:**
- `OTC` - Over-the-counter (no prescription needed)
- `Schedule H` - Prescription required
- `Schedule H1` - Prescription required with special tracking
- `Schedule X` - Narcotic drugs (strictly controlled)

**Example Medicine Data:**
```json
[
  {
    "name": "Paracetamol",
    "dosage_form": "Tablet",
    "therapeutic_category_id": "<PAIN_RELIEF_CATEGORY_ID>",
    "is_prescription_required": false,
    "is_controlled": false,
    "schedule_type": "OTC",
    "description": "Pain reliever and fever reducer"
  },
  {
    "name": "Amoxicillin",
    "dosage_form": "Capsule",
    "therapeutic_category_id": "<ANTIBIOTIC_CATEGORY_ID>",
    "is_prescription_required": true,
    "is_controlled": false,
    "schedule_type": "Schedule H",
    "description": "Antibiotic for bacterial infections"
  }
]
```

#### B. Medicine Compositions (removed)

The **Medicine Compositions** CRUD API and admin UI were removed from the application. A legacy `medicine_compositions` table may still exist in older databases; you can document active ingredients in the medicine **description** or omit this layer for new deployments.

#### C. Medicine Brands

**Data to Collect for Each Brand:**

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| `medicine_id` | ✅ Yes | Medicine UUID | Get from medicines |
| `brand_name` | ✅ Yes | Brand name | `"Crocin"`, `"Calpol"`, `"Dolo-650"` |
| `manufacturer` | ✅ Yes | Manufacturer name | `"GSK"`, `"Cipla"`, `"Sun Pharma"` |
| `mrp` | ✅ Yes | Maximum Retail Price (₹) | `25.50`, `45.00` |
| `description` | ❌ No | Brand description | `"Paracetamol 500mg tablet"` |
| `image_url` | ❌ No | Medicine image URL | `"https://example.com/images/crocin.jpg"` |
| `barcode` | ❌ No | Product barcode | `"8901030865147"` |

**Note:** Currently, the system doesn't have an `image_url` or `barcode` field in the database. You may want to:
1. Store images externally (cloud storage) and store URLs
2. Add these fields to the database schema if needed

**Example Brand Data:**
```json
[
  {
    "medicine_id": "<PARACETAMOL_MEDICINE_ID>",
    "brand_name": "Crocin",
    "manufacturer": "GSK",
    "mrp": 25.50,
    "description": "Paracetamol 500mg tablet",
    "image_url": "https://your-cdn.com/medicines/crocin.jpg",
    "barcode": "8901030865147"
  },
  {
    "medicine_id": "<PARACETAMOL_MEDICINE_ID>",
    "brand_name": "Calpol",
    "manufacturer": "GSK",
    "mrp": 28.00,
    "description": "Paracetamol 500mg tablet",
    "image_url": "https://your-cdn.com/medicines/calpol.jpg",
    "barcode": "8901030865154"
  },
  {
    "medicine_id": "<PARACETAMOL_MEDICINE_ID>",
    "brand_name": "Dolo-650",
    "manufacturer": "Micro Labs",
    "mrp": 30.00,
    "description": "Paracetamol 650mg tablet",
    "image_url": "https://your-cdn.com/medicines/dolo650.jpg",
    "barcode": "8901030865161"
  }
]
```

---

## 4. Medicine Images/Pictures

### Master Data Required

**Purpose:** Visual identification of medicines for staff and customers

### Image Requirements

**File Format:**
- **Recommended:** JPEG, PNG, WebP
- **Max File Size:** 2MB per image
- **Dimensions:** 
  - Minimum: 300x300 pixels
  - Recommended: 800x800 pixels
  - Maximum: 2000x2000 pixels
- **Aspect Ratio:** Square (1:1) preferred

**Image Storage Options:**

#### Option 1: External Storage (Recommended)
- Store images on cloud storage (AWS S3, Google Cloud Storage, Azure Blob)
- Store image URLs in database or separate table
- **Pros:** Scalable, fast, doesn't bloat database
- **Cons:** Requires cloud storage setup

#### Option 2: Database Storage
- Store images as base64 or binary in database
- **Pros:** Simple, all data in one place
- **Cons:** Slower, increases database size

#### Option 3: Local File System
- Store images in server file system
- Serve via static file server
- **Pros:** Simple setup
- **Cons:** Not scalable, backup complexity

### Image Data to Collect

For each medicine brand, collect:

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| `medicine_brand_id` | ✅ Yes | Brand UUID | Get from medicine brands |
| `image_url` | ✅ Yes | Full URL to image | `"https://cdn.example.com/medicines/crocin.jpg"` |
| `image_type` | ❌ No | Image type | `"product"`, `"packaging"`, `"both"` |
| `alt_text` | ❌ No | Alternative text | `"Crocin 500mg tablet"` |

**Example Image Data:**
```json
[
  {
    "medicine_brand_id": "<CROCIN_BRAND_ID>",
    "image_url": "https://your-cdn.com/medicines/crocin-front.jpg",
    "image_type": "product",
    "alt_text": "Crocin 500mg tablet front view"
  },
  {
    "medicine_brand_id": "<CROCIN_BRAND_ID>",
    "image_url": "https://your-cdn.com/medicines/crocin-back.jpg",
    "image_type": "packaging",
    "alt_text": "Crocin 500mg tablet back view"
  }
]
```

### Image Naming Convention

**Recommended naming pattern:**
```
{manufacturer}_{brand_name}_{strength}_{dosage_form}.jpg

Examples:
- gsk_crocin_500mg_tablet.jpg
- cipla_amoxil_250mg_capsule.jpg
- sun_pharma_dolo_650mg_tablet.jpg
```

---

## 5. User Accounts

### Master Data Required

**Purpose:** Staff and pharmacist accounts for system access

### Data to Collect for Each User

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| `role_id` | ✅ Yes | Role UUID | Get from roles |
| `full_name` | ✅ Yes | Full name | `"Dr. Rahul Sharma"` |
| `mobile_number` | ✅ Yes | Mobile number | `"9876543210"` |
| `email` | ✅ Yes | Email (unique) | `"rahul@pharmacy.com"` |
| `password` | ✅ Yes | Password (will be hashed) | `"SecurePassword123!"` |
| `is_pharmacist` | ✅ Yes | Is licensed pharmacist? | `true` or `false` |

### Pharmacist-Specific Data

If `is_pharmacist = true`, also collect:

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| `license_number` | ✅ Yes | Pharmacist license number | `"PHARMA-AP-12345"` |
| `license_valid_till` | ✅ Yes | License expiry date | `"2027-12-31"` |

**Example User Data:**
```json
[
  {
    "role_id": "<PHARMACIST_ROLE_ID>",
    "full_name": "Dr. Rahul Sharma",
    "mobile_number": "9876543210",
    "email": "rahul@pharmacy.com",
    "password": "SecurePassword123!",
    "is_pharmacist": true,
    "license_number": "PHARMA-AP-12345",
    "license_valid_till": "2027-12-31"
  },
  {
    "role_id": "<CASHIER_ROLE_ID>",
    "full_name": "Priya Patel",
    "mobile_number": "9876543211",
    "email": "priya@pharmacy.com",
    "password": "SecurePassword123!",
    "is_pharmacist": false
  }
]
```

---

## Master Data Import Template

### CSV/Excel Template Structure

#### 1. Therapeutic Categories Template

| name | description |
|------|-------------|
| Antibiotic | Drugs used to treat bacterial infections |
| Pain Reliever | Medicines for pain management |

#### 2. Medicines Template

| name | dosage_form | therapeutic_category_name | is_prescription_required | is_controlled | schedule_type | description |
|------|-------------|----------------------------|-------------------------|---------------|---------------|-------------|
| Paracetamol | Tablet | Pain Reliever | false | false | OTC | Pain reliever and fever reducer |
| Amoxicillin | Capsule | Antibiotic | true | false | Schedule H | Antibiotic for bacterial infections |

#### 3. Medicine Brands Template

| medicine_name | brand_name | manufacturer | mrp | description | image_url | barcode |
|---------------|------------|--------------|-----|-------------|-----------|---------|
| Paracetamol | Crocin | GSK | 25.50 | Paracetamol 500mg tablet | https://cdn.example.com/crocin.jpg | 8901030865147 |
| Paracetamol | Calpol | GSK | 28.00 | Paracetamol 500mg tablet | https://cdn.example.com/calpol.jpg | 8901030865154 |

---

## Master Data Setup Order

### Recommended Sequence:

1. **Step 1: Roles and Permissions**
   - Create roles
   - Create permissions
   - Map roles to permissions

2. **Step 2: Therapeutic Categories**
   - Create all medicine categories

3. **Step 3: Medicines**
   - Create generic medicines (optionally describe salts/strengths in the description field)

4. **Step 4: Medicine Brands**
   - Create branded versions
   - Upload/configure medicine images

5. **Step 5: User Accounts**
   - Create staff accounts
   - Create pharmacist profiles

6. **Step 6: Initial Inventory**
   - Load `product_batches` rows for existing stock (database; no public batch CRUD API)

---

## Data Collection Checklist

Before importing master data, ensure you have:

### Roles & Permissions
- [ ] List of all user roles needed
- [ ] List of all permissions needed
- [ ] Role-permission mapping

### Therapeutic Categories
- [ ] Complete list of medicine categories
- [ ] Category descriptions

### Medicine Catalog
- [ ] List of all generic medicines
- [ ] Dosage forms for each medicine
- [ ] Brand names for each medicine
- [ ] Manufacturer information
- [ ] MRP (Maximum Retail Price) for each brand
- [ ] Medicine images/pictures
- [ ] Barcodes (if available)

### User Accounts
- [ ] Staff member details (name, email, mobile)
- [ ] Role assignment for each staff member
- [ ] Pharmacist license information (if applicable)

### Images
- [ ] Medicine images in required format
- [ ] Image storage solution configured
- [ ] Image URLs or file paths

---

## Notes

1. **Medicine Images:** Currently, the database schema doesn't include image fields. You may need to:
   - Add `image_url` field to `medicine_brands` table, OR
   - Create a separate `medicine_images` table, OR
   - Store images externally and reference URLs

2. **Barcodes:** Consider adding barcode field to `medicine_brands` for inventory scanning

3. **Batch Import:** For large catalogs, consider creating bulk import endpoints or scripts

4. **Data Validation:** Validate all master data before import:
   - Check for duplicates
   - Verify foreign key relationships
   - Validate image URLs are accessible
   - Ensure MRP values are positive

5. **Backup:** Always backup master data before bulk imports

---

## Support

For questions about master data setup:
- Refer to API documentation at `/docs`
- Check `Client_Data_Collection_Requirements.md` for field-level details
- Contact support for bulk import assistance
