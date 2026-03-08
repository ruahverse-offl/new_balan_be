# Medical Shop Pharmacy Management System - API Documentation

## Overview

This is a comprehensive backend API for managing a medical shop/pharmacy system. The API provides full CRUD (Create, Read, Update, Delete) operations for managing roles, users, medicines, orders, payments, and inventory. It also includes comprehensive dashboard endpoints for analytics and business intelligence.

**Base URL:** `http://localhost:8000`  
**API Version:** `v1`  
**API Prefix:** `/api/v1`

## Table of Contents

1. [Getting Started](#getting-started)
2. [API Endpoints](#api-endpoints)
   - [Roles](#1-roles)
   - [Permissions](#2-permissions)
   - [Role Permissions](#3-role-permissions)
   - [Users](#4-users)
   - [Pharmacist Profiles](#5-pharmacist-profiles)
   - [Therapeutic Categories](#6-therapeutic-categories)
   - [Medicine Compositions](#7-medicine-compositions)
   - [Medicines](#8-medicines)
   - [Medicine Brands](#9-medicine-brands)
   - [Product Batches](#10-product-batches)
   - [Inventory Transactions](#11-inventory-transactions)
   - [Orders](#12-orders)
   - [Payments](#13-payments)
   - [Dashboards](#14-dashboards)
   - [Razorpay Payment Gateway](#15-razorpay-payment-gateway)
3. [Common Features](#common-features)
4. [Error Handling](#error-handling)

---

## Getting Started

### Prerequisites

- Python 3.11.0
- PostgreSQL database
- Virtual environment (recommended)

### Installation

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the backend root (copy from `.env.example`). Required and optional variables:

```env
# Database (required)
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Application
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=your-secret-key-change-in-production

# CORS (comma-separated origins, or * for all)
CORS_ORIGINS=*

# Razorpay Payment Gateway (required for online payments)
# Get keys from https://dashboard.razorpay.com
RAZORPAY_KEY_ID=rzp_test_xxxxxxxx
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
```

See `.env.example` for the full list. **Razorpay:** Use test keys for development; set live keys in production.

### Running the Application

**Local (with venv):**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Docker:** From the project root (`new_balan_web/`), run `docker-compose up` to start the backend, PostgreSQL, and nginx. Ensure `backend/.env` exists (copy from `backend/.env.example`).

The API will be available at:
- **API:** http://localhost:8000
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## API Endpoints

### Common Query Parameters

All list endpoints support the following query parameters:

- `limit` (int, default: 20, range: 1-100): Number of records per page
- `offset` (int, default: 0): Number of records to skip (for pagination)
- `search` (string, optional): Search term to match against searchable fields
- `sort_by` (string, default: "created_at"): Field name to sort by
- `sort_order` (string, default: "desc"): Sort order - "asc" or "desc"

### Common Response Format

**List Response:**
```json
{
  "items": [...],
  "pagination": {
    "total": 100,
    "limit": 20,
    "offset": 0,
    "has_next": true,
    "has_previous": false
  }
}
```

**Single Item Response:**
```json
{
  "id": "uuid",
  "field1": "value1",
  "field2": "value2",
  "created_by": "uuid",
  "created_at": "2026-02-01T10:30:00Z",
  "created_ip": "192.168.1.100",
  "updated_by": "uuid",
  "updated_at": "2026-02-01T11:00:00Z",
  "updated_ip": "192.168.1.100",
  "is_deleted": false
}
```

---

## 1. Roles

**Base Path:** `/api/v1/roles`

### Purpose
Roles define different user types in the system (e.g., Pharmacist, Admin, Cashier). They are used for Role-Based Access Control (RBAC) to manage what actions users can perform.

### Why We Need Roles
- **Access Control:** Different users need different permissions (pharmacist can approve prescriptions, cashier can only process payments)
- **Security:** Prevents unauthorized access to sensitive operations
- **Organization:** Groups users by their responsibilities and capabilities

### Endpoints

#### Create Role
**POST** `/api/v1/roles/`

Creates a new role in the system.

**Request Body:**
```json
{
  "name": "PHARMACIST",
  "description": "Licensed pharmacist who can review and approve prescriptions"
}
```

**What You Can Create:**
- `PHARMACIST` - Licensed pharmacist role for prescription review and approval
- `ADMIN` - System administrator with full access
- `CASHIER` - Cashier role for processing payments
- `MANAGER` - Store manager role for inventory and operations management
- `CUSTOMER_SERVICE` - Customer service representative role

**Response:** 201 Created
```json
{
  "id": "b1f9e123-4567-8901-2345-678901234567",
  "name": "PHARMACIST",
  "description": "Licensed pharmacist who can review and approve prescriptions",
  "is_active": true,
  "created_by": "uuid",
  "created_at": "2026-02-01T10:30:00Z",
  "created_ip": "192.168.1.100",
  "is_deleted": false
}
```

#### Get Role by ID
**GET** `/api/v1/roles/{role_id}`

Retrieves a specific role by its UUID.

**Response:** 200 OK

#### Get Roles List
**GET** `/api/v1/roles/`

Retrieves a paginated list of roles with search and sort capabilities.

**Example:**
```
GET /api/v1/roles/?limit=10&offset=0&search=PHARMACIST&sort_by=name&sort_order=asc
```

#### Update Role
**PATCH** `/api/v1/roles/{role_id}`

Updates an existing role. All fields are optional.

**Request Body:**
```json
{
  "name": "SENIOR_PHARMACIST",
  "description": "Senior licensed pharmacist with additional privileges"
}
```

**Response:** 200 OK

#### Delete Role (Soft Delete)
**DELETE** `/api/v1/roles/{role_id}`

Soft deletes a role (sets `is_deleted = true`). The role is not physically removed from the database.

**Response:** 200 OK
```json
{
  "message": "Role deleted successfully",
  "id": "b1f9e123-4567-8901-2345-678901234567"
}
```

---

## 2. Permissions

**Base Path:** `/api/v1/permissions`

### Purpose
Permissions define specific actions that can be performed in the system (e.g., "PRESCRIPTION_REVIEW", "INVENTORY_UPDATE"). They are granular access controls that can be assigned to roles.

### Why We Need Permissions
- **Granular Control:** Fine-grained access control beyond just roles
- **Flexibility:** Allows customizing what each role can do
- **Security:** Ensures users can only perform authorized actions
- **Audit Trail:** Tracks what permissions are assigned to which roles

### Endpoints

#### Create Permission
**POST** `/api/v1/permissions/`

Creates a new permission.

**Request Body:**
```json
{
  "code": "PRESCRIPTION_REVIEW",
  "description": "Can review and validate prescriptions"
}
```

**What You Can Create:**
- `PRESCRIPTION_REVIEW` - Review and validate prescriptions
- `PRESCRIPTION_APPROVE` - Approve prescriptions for dispensing
- `INVENTORY_VIEW` - View inventory levels
- `INVENTORY_UPDATE` - Update inventory quantities
- `ORDER_CREATE` - Create new orders
- `ORDER_CANCEL` - Cancel existing orders
- `PAYMENT_PROCESS` - Process payments
- `USER_MANAGE` - Manage user accounts
- `REPORT_VIEW` - View reports and analytics

**Response:** 201 Created

#### Get Permission by ID
**GET** `/api/v1/permissions/{permission_id}`

#### Get Permissions List
**GET** `/api/v1/permissions/`

#### Update Permission
**PATCH** `/api/v1/permissions/{permission_id}`

#### Delete Permission (Soft Delete)
**DELETE** `/api/v1/permissions/{permission_id}`

---

## 3. Role Permissions

**Base Path:** `/api/v1/role-permissions`

### Purpose
Role Permissions link roles to permissions, creating a many-to-many relationship. This allows you to assign multiple permissions to a role and vice versa.

### Why We Need Role Permissions
- **Role Configuration:** Defines what each role can do by assigning permissions
- **Flexible Access Control:** Easy to modify role capabilities without changing user assignments
- **RBAC Implementation:** Core component of Role-Based Access Control system

### Endpoints

#### Create Role Permission
**POST** `/api/v1/role-permissions/`

Assigns a permission to a role.

**Request Body:**
```json
{
  "role_id": "b1f9e123-4567-8901-2345-678901234567",
  "permission_id": "p9x3e123-4567-8901-2345-678901234567"
}
```

**What You Can Create:**
- Link `PHARMACIST` role to `PRESCRIPTION_REVIEW` permission
- Link `PHARMACIST` role to `PRESCRIPTION_APPROVE` permission
- Link `CASHIER` role to `PAYMENT_PROCESS` permission
- Link `ADMIN` role to all permissions

**Response:** 201 Created

#### Get Role Permission by ID
**GET** `/api/v1/role-permissions/{role_permission_id}`

#### Get Role Permissions List
**GET** `/api/v1/role-permissions/`

#### Update Role Permission
**PATCH** `/api/v1/role-permissions/{role_permission_id}`

#### Delete Role Permission (Soft Delete)
**DELETE** `/api/v1/role-permissions/{role_permission_id}`

---

## 4. Users

**Base Path:** `/api/v1/users`

### Purpose
Users represent people who interact with the system (pharmacists, cashiers, managers, customers). Each user is assigned a role that determines their access level.

### Why We Need Users
- **System Access:** Users are the entities that log in and use the system
- **Authentication:** Required for secure access to the pharmacy system
- **Account Management:** Tracks who performs what actions in the system
- **Personalization:** Associates actions and data with specific individuals

### Endpoints

#### Create User
**POST** `/api/v1/users/`

Creates a new user account.

**Request Body:**
```json
{
  "role_id": "b1f9e123-4567-8901-2345-678901234567",
  "full_name": "Rahul Sharma",
  "mobile_number": "9876543210",
  "email": "rahul@gmail.com",
  "password_hash": "$2b$10$..."
}
```

**What You Can Create:**
- **Pharmacist Users:** Staff members who can review prescriptions
- **Cashier Users:** Staff who process payments
- **Manager Users:** Store managers who oversee operations
- **Customer Users:** End customers who place orders
- **Admin Users:** System administrators

**Note:** `is_active` is automatically set to `true` by the backend.

**Response:** 201 Created

#### Get User by ID
**GET** `/api/v1/users/{user_id}`

#### Get Users List
**GET** `/api/v1/users/`

#### Update User
**PATCH** `/api/v1/users/{user_id}`

**Request Body:**
```json
{
  "full_name": "Rahul Kumar Sharma",
  "mobile_number": "9876543211"
}
```

#### Delete User (Soft Delete)
**DELETE** `/api/v1/users/{user_id}`

---

## 5. Pharmacist Profiles

**Base Path:** `/api/v1/pharmacist-profiles`

### Purpose
Pharmacist Profiles store additional information about users who are licensed pharmacists, including their license numbers and validity dates. This is required for regulatory compliance.

### Why We Need Pharmacist Profiles
- **Regulatory Compliance:** Tracks pharmacist licenses for legal requirements
- **License Validation:** Ensures only licensed pharmacists can approve prescriptions
- **Audit Requirements:** Maintains records of who is authorized to dispense medicines
- **Professional Credentials:** Stores professional information separate from basic user data

### Endpoints

#### Create Pharmacist Profile
**POST** `/api/v1/pharmacist-profiles/`

Creates a pharmacist profile for a user.

**Request Body:**
```json
{
  "user_id": "u123e456-7890-1234-5678-901234567890",
  "license_number": "PHARMA-AP-12345",
  "license_valid_till": "2027-12-31"
}
```

**What You Can Create:**
- Pharmacist profiles linked to user accounts
- License information for regulatory compliance
- Validity tracking for license expiration

**Response:** 201 Created

#### Get Pharmacist Profile by ID
**GET** `/api/v1/pharmacist-profiles/{user_id}`

#### Get Pharmacist Profiles List
**GET** `/api/v1/pharmacist-profiles/`

#### Update Pharmacist Profile
**PATCH** `/api/v1/pharmacist-profiles/{user_id}`

#### Delete Pharmacist Profile (Soft Delete)
**DELETE** `/api/v1/pharmacist-profiles/{user_id}`

---

## 6. Therapeutic Categories

**Base Path:** `/api/v1/therapeutic-categories`

### Purpose
Therapeutic Categories classify medicines by their medical purpose (e.g., Antibiotics, Pain Relievers, Antacids). This helps in organizing medicines and making them easier to find.

### Why We Need Therapeutic Categories
- **Medicine Organization:** Groups medicines by their therapeutic use
- **Easy Search:** Helps customers and staff find medicines by category
- **Inventory Management:** Organizes inventory by medical purpose
- **Reporting:** Enables category-wise sales and inventory reports

### Endpoints

#### Create Therapeutic Category
**POST** `/api/v1/therapeutic-categories/`

Creates a new therapeutic category.

**Request Body:**
```json
{
  "name": "Antibiotic",
  "description": "Drugs used to treat bacterial infections"
}
```

**What You Can Create:**
- `Antibiotic` - For treating bacterial infections
- `Pain Reliever` - For pain management (e.g., Paracetamol, Ibuprofen)
- `Antacid` - For treating acidity and indigestion
- `Antihistamine` - For allergies and cold symptoms
- `Vitamin` - Nutritional supplements
- `Cardiac` - Heart-related medicines
- `Diabetes` - Diabetes management medicines

**Response:** 201 Created

#### Get Therapeutic Category by ID
**GET** `/api/v1/therapeutic-categories/{category_id}`

#### Get Therapeutic Categories List
**GET** `/api/v1/therapeutic-categories/`

#### Update Therapeutic Category
**PATCH** `/api/v1/therapeutic-categories/{category_id}`

#### Delete Therapeutic Category (Soft Delete)
**DELETE** `/api/v1/therapeutic-categories/{category_id}`

---

## 7. Medicine Compositions

**Base Path:** `/api/v1/medicine-compositions`

### Purpose
Medicine Compositions define the active ingredients (salts) and their strengths in a medicine. A single medicine can have multiple compositions (e.g., Paracetamol 500mg + Caffeine 65mg).

### Why We Need Medicine Compositions
- **Ingredient Tracking:** Records what active ingredients are in each medicine
- **Strength Information:** Stores dosage strength (e.g., 500mg, 250mg)
- **Allergy Management:** Helps identify medicines with specific ingredients for allergy patients
- **Regulatory Compliance:** Required for proper medicine labeling and documentation

### Endpoints

#### Create Medicine Composition
**POST** `/api/v1/medicine-compositions/`

Creates a composition entry for a medicine.

**Request Body:**
```json
{
  "medicine_id": "m1e123-4567-8901-2345-678901234567",
  "salt_name": "Paracetamol",
  "strength": "500",
  "unit": "mg"
}
```

**What You Can Create:**
- Single salt compositions: `Paracetamol 500mg`
- Multiple salt compositions: `Paracetamol 500mg + Caffeine 65mg`
- Different strengths: `Paracetamol 250mg`, `Paracetamol 500mg`, `Paracetamol 650mg`
- Different units: `mg`, `ml`, `g`, `IU`

**Response:** 201 Created

#### Get Medicine Composition by ID
**GET** `/api/v1/medicine-compositions/{composition_id}`

#### Get Medicine Compositions List
**GET** `/api/v1/medicine-compositions/`

#### Update Medicine Composition
**PATCH** `/api/v1/medicine-compositions/{composition_id}`

#### Delete Medicine Composition (Soft Delete)
**DELETE** `/api/v1/medicine-compositions/{composition_id}`

---

## 8. Medicines

**Base Path:** `/api/v1/medicines`

### Purpose
Medicines represent the base medicine entity (e.g., "Paracetamol", "Amoxicillin"). This is the generic medicine name before it's associated with specific brands.

### Why We Need Medicines
- **Generic Medicine Management:** Tracks medicines by their generic names
- **Brand Association:** Links to multiple brands of the same medicine
- **Prescription Requirements:** Tracks if prescription is required
- **Schedule Classification:** Categorizes medicines by regulatory schedule (OTC, Schedule H, etc.)

### Endpoints

#### Create Medicine
**POST** `/api/v1/medicines/`

Creates a new medicine entry.

**Request Body:**
```json
{
  "name": "Paracetamol",
  "dosage_form": "Tablet",
  "therapeutic_category_id": "tc1e123-4567-8901-2345-678901234567",
  "is_prescription_required": false,
  "is_controlled": false,
  "schedule_type": "OTC",
  "description": "Pain reliever and fever reducer"
}
```

**What You Can Create:**
- **OTC Medicines:** Over-the-counter medicines (e.g., Paracetamol, Ibuprofen)
- **Prescription Medicines:** Require doctor's prescription (e.g., Antibiotics)
- **Controlled Substances:** Regulated medicines (e.g., Narcotics)
- **Different Dosage Forms:** Tablets, Capsules, Syrups, Injections, Ointments

**Dosage Forms:**
- `Tablet` - Solid oral form
- `Capsule` - Gelatin-coated form
- `Syrup` - Liquid oral form
- `Injection` - Injectable form
- `Ointment` - Topical application
- `Drops` - Liquid drops

**Schedule Types:**
- `OTC` - Over-the-counter (no prescription needed)
- `Schedule H` - Prescription required
- `Schedule H1` - Prescription required with special tracking
- `Schedule X` - Narcotic drugs

**Response:** 201 Created

#### Get Medicine by ID
**GET** `/api/v1/medicines/{medicine_id}`

#### Get Medicines List
**GET** `/api/v1/medicines/`

#### Update Medicine
**PATCH** `/api/v1/medicines/{medicine_id}`

#### Delete Medicine (Soft Delete)
**DELETE** `/api/v1/medicines/{medicine_id}`

---

## 9. Medicine Brands

**Base Path:** `/api/v1/medicine-brands`

### Purpose
Medicine Brands represent specific branded versions of a generic medicine (e.g., "Crocin" is a brand of Paracetamol). Different brands of the same medicine may have different prices and manufacturers.

### Why We Need Medicine Brands
- **Brand Management:** Tracks different brands of the same medicine
- **Pricing:** Each brand can have different MRP (Maximum Retail Price)
- **Manufacturer Tracking:** Records which company manufactures each brand
- **Customer Choice:** Allows customers to choose preferred brands

### Endpoints

#### Create Medicine Brand
**POST** `/api/v1/medicine-brands/`

Creates a new medicine brand.

**Request Body:**
```json
{
  "medicine_id": "m1e123-4567-8901-2345-678901234567",
  "brand_name": "Crocin",
  "manufacturer": "GSK",
  "mrp": 25.50,
  "description": "Paracetamol 500mg tablet"
}
```

**What You Can Create:**
- **Paracetamol Brands:** Crocin, Calpol, Dolo-650, Tylenol
- **Amoxicillin Brands:** Amoxil, Mox, Amoxycillin
- **Different Manufacturers:** GSK, Cipla, Sun Pharma, etc.
- **Price Variations:** Same medicine, different brands, different prices

**Response:** 201 Created

#### Get Medicine Brand by ID
**GET** `/api/v1/medicine-brands/{brand_id}`

#### Get Medicine Brands List
**GET** `/api/v1/medicine-brands/`

#### Update Medicine Brand
**PATCH** `/api/v1/medicine-brands/{brand_id}`

#### Delete Medicine Brand (Soft Delete)
**DELETE** `/api/v1/medicine-brands/{brand_id}`

---

## 10. Product Batches

**Base Path:** `/api/v1/product-batches`

### Purpose
Product Batches track specific batches of medicine brands with their manufacturing dates, expiry dates, purchase prices, and available quantities. This is essential for inventory management and expiry tracking.

### Why We Need Product Batches
- **Expiry Management:** Tracks expiry dates to prevent selling expired medicines
- **Batch Tracking:** Enables recall of specific batches if needed
- **Inventory Control:** Manages quantities of each batch separately
- **Cost Tracking:** Records purchase price for profit calculation
- **FIFO/LIFO:** Supports First-In-First-Out or Last-In-First-Out inventory methods

### Endpoints

#### Create Product Batch
**POST** `/api/v1/product-batches/`

Creates a new product batch.

**Request Body:**
```json
{
  "medicine_brand_id": "mb1e123-4567-8901-2345-678901234567",
  "batch_number": "BATCH-0925",
  "expiry_date": "2026-09-30",
  "purchase_price": 18.50,
  "quantity_available": 120
}
```

**What You Can Create:**
- Batches with different expiry dates
- Batches with different purchase prices
- Batches with varying quantities
- Batch numbers for tracking and recall purposes

**Response:** 201 Created

#### Get Product Batch by ID
**GET** `/api/v1/product-batches/{batch_id}`

#### Get Product Batches List
**GET** `/api/v1/product-batches/`

#### Update Product Batch
**PATCH** `/api/v1/product-batches/{batch_id}`

**Request Body:**
```json
{
  "quantity_available": 100
}
```

#### Delete Product Batch (Soft Delete)
**DELETE** `/api/v1/product-batches/{batch_id}`

---

## 11. Inventory Transactions

**Base Path:** `/api/v1/inventory-transactions`

### Purpose
Inventory Transactions record all movements of stock (additions, sales, returns, adjustments). This creates a complete audit trail of inventory changes.

### Why We Need Inventory Transactions
- **Audit Trail:** Complete record of all inventory movements
- **Stock Tracking:** Know exactly when and why stock changed
- **Reconciliation:** Helps reconcile physical stock with system stock
- **Loss Tracking:** Identifies theft, damage, or expiry losses
- **Reporting:** Enables inventory movement reports and analytics

### Endpoints

#### Create Inventory Transaction
**POST** `/api/v1/inventory-transactions/`

Creates a new inventory transaction.

**Request Body:**
```json
{
  "medicine_brand_id": "mb1e123-4567-8901-2345-678901234567",
  "product_batch_id": "pb1e123-4567-8901-2345-678901234567",
  "transaction_type": "SALE",
  "quantity_change": -10,
  "reference_order_id": "o1e123-4567-8901-2345-678901234567",
  "remarks": "Sold to customer"
}
```

**What You Can Create:**
- **SALE:** When medicine is sold (negative quantity)
- **PURCHASE:** When new stock is purchased (positive quantity)
- **RETURN:** When customer returns medicine (positive quantity)
- **ADJUSTMENT:** Stock adjustments for discrepancies
- **EXPIRY:** When stock expires (negative quantity)
- **DAMAGE:** When stock is damaged (negative quantity)

**Transaction Types:**
- `SALE` - Medicine sold to customer
- `PURCHASE` - New stock purchased
- `RETURN` - Customer return
- `ADJUSTMENT` - Manual stock adjustment
- `EXPIRY` - Expired stock removal
- `DAMAGE` - Damaged stock removal

**Response:** 201 Created

#### Get Inventory Transaction by ID
**GET** `/api/v1/inventory-transactions/{transaction_id}`

#### Get Inventory Transactions List
**GET** `/api/v1/inventory-transactions/`

#### Update Inventory Transaction
**PATCH** `/api/v1/inventory-transactions/{transaction_id}`

#### Delete Inventory Transaction (Soft Delete)
**DELETE** `/api/v1/inventory-transactions/{transaction_id}`

---

## 12. Orders

**Base Path:** `/api/v1/orders`

### Purpose
Orders represent customer orders for medicines. They track the order status, approval status, and link to customers and payments.

### Why We Need Orders
- **Order Management:** Tracks all customer orders from creation to fulfillment
- **Status Tracking:** Monitors order progress (Pending, Approved, Dispensed, Completed)
- **Prescription Handling:** Manages prescription-based orders
- **Customer History:** Maintains order history for each customer
- **Business Operations:** Core entity for pharmacy operations

### Endpoints

#### Create Order
**POST** `/api/v1/orders/`

Creates a new order.

**Request Body:**
```json
{
  "customer_id": "u123e456-7890-1234-5678-901234567890",
  "order_source": "PRESCRIPTION",
  "order_status": "PENDING",
  "approval_status": "PENDING"
}
```

**What You Can Create:**
- **Prescription Orders:** Orders based on doctor's prescription
- **OTC Orders:** Over-the-counter orders without prescription
- **Walk-in Orders:** In-store orders
- **Online Orders:** Orders placed through online platform

**Order Sources:**
- `PRESCRIPTION` - Based on doctor's prescription
- `OTC` - Over-the-counter (no prescription)
- `WALK_IN` - In-store purchase
- `ONLINE` - Online order

**Order Status:**
- `PENDING` - Order created, awaiting processing
- `APPROVED` - Order approved by pharmacist
- `DISPENSED` - Medicine dispensed to customer
- `COMPLETED` - Order completed with payment
- `CANCELLED` - Order cancelled

**Approval Status:**
- `PENDING` - Awaiting pharmacist approval
- `APPROVED` - Approved by pharmacist
- `REJECTED` - Rejected by pharmacist

**Response:** 201 Created

#### Get Order by ID
**GET** `/api/v1/orders/{order_id}`

#### Get Orders List
**GET** `/api/v1/orders/`

#### Update Order
**PATCH** `/api/v1/orders/{order_id}`

**Request Body:**
```json
{
  "order_status": "APPROVED",
  "approval_status": "APPROVED"
}
```

#### Delete Order (Soft Delete)
**DELETE** `/api/v1/orders/{order_id}`

---

## 13. Payments

**Base Path:** `/api/v1/payments`

### Purpose
Payments record financial transactions for orders. They track payment method, status, and amount paid.

### Why We Need Payments
- **Financial Tracking:** Records all payments received
- **Payment Methods:** Tracks different payment methods (Cash, UPI, Card, etc.)
- **Reconciliation:** Helps reconcile cash and digital payments
- **Reporting:** Enables financial reports and revenue tracking
- **Order Completion:** Links payments to orders for order fulfillment

### Endpoints

#### Create Payment
**POST** `/api/v1/payments/`

Creates a new payment record.

**Request Body:**
```json
{
  "order_id": "o1e123-4567-8901-2345-678901234567",
  "payment_method": "UPI",
  "payment_status": "PENDING",
  "amount": 299.00
}
```

**What You Can Create:**
- **Cash Payments:** Physical cash transactions
- **UPI Payments:** Digital payments via UPI
- **Card Payments:** Credit/Debit card payments
- **Wallet Payments:** Digital wallet payments
- **Partial Payments:** Multiple payments for a single order

**Payment Methods:**
- `RAZORPAY` - Online payments (UPI, cards, net banking) via Razorpay
- `CASH` - Physical cash
- `UPI` - Unified Payments Interface (manual entry)
- `CARD` - Credit/Debit card (manual entry)
- `WALLET` - Digital wallet
- `NET_BANKING` - Online banking transfer

**Payment Status:**
- `PENDING` - Payment initiated but not completed
- `COMPLETED` - Payment successfully completed
- `FAILED` - Payment failed
- `REFUNDED` - Payment refunded to customer

**Response:** 201 Created

#### Get Payment by ID
**GET** `/api/v1/payments/{payment_id}`

#### Get Payments List
**GET** `/api/v1/payments/`

#### Update Payment
**PATCH** `/api/v1/payments/{payment_id}`

**Request Body:**
```json
{
  "payment_status": "COMPLETED"
}
```

#### Delete Payment (Soft Delete)
**DELETE** `/api/v1/payments/{payment_id}`

---

## 14. Dashboards

**Base Path:** `/api/v1/dashboards`

### Purpose
Dashboards provide comprehensive analytics and insights for different aspects of the pharmacy management system. They include Key Performance Indicators (KPIs), alerts, and chart data for visualization.

### Why We Need Dashboards
- **Business Intelligence:** Real-time insights into business performance
- **Decision Making:** Data-driven decisions for inventory, sales, and operations
- **Monitoring:** Track KPIs and identify issues through alerts
- **Reporting:** Visual representation of trends and patterns
- **Performance Tracking:** Monitor growth rates, fulfillment rates, and other metrics

### Dashboard Types

#### 1. Finance Dashboard
**Base Path:** `/api/v1/dashboards/finance`

##### Get Finance Dashboard
**GET** `/api/v1/dashboards/finance/`

Retrieves financial analytics including revenue, orders, payments, and growth metrics.

**Query Parameters:**
- `period` (string, default: "month"): KPI period - `today`, `week`, `month`, `quarter`, `year`
- `trend_period` (string, default: "30d"): Trend period - `7d`, `30d`, `3m`, `6m`, `1y`
- `trend_granularity` (string, default: "daily"): Trend granularity - `daily`, `weekly`, `monthly`
- `include_charts` (boolean, default: true): Include chart data in response
- `monthly_trend_months` (int, default: 12, range: 1-36): Number of months for monthly trend

**Response:** 200 OK
```json
{
  "kpis": {
    "total_revenue": 5000000.00,
    "today_revenue": 50000.00,
    "month_revenue": 1500000.00,
    "year_revenue": 5000000.00,
    "total_orders": 5000,
    "today_orders": 50,
    "month_orders": 1500,
    "pending_orders": 25,
    "completed_orders": 4500,
    "average_order_value": 1111.11,
    "revenue_growth_rate": 15.5,
    "payment_success_rate": 98.5,
    "outstanding_payments": 25000.00
  },
  "alerts": [
    {
      "type": "LOW_REVENUE",
      "severity": "WARNING",
      "message": "Today's revenue is 20% below average",
      "today_revenue": 50000.00,
      "average_daily_revenue": 62500.00,
      "percentage_below": 20.0
    }
  ],
  "charts": {
    "revenue_trend": [
      {"date": "2026-01-01", "revenue": 50000.00}
    ],
    "orders_trend": [
      {"date": "2026-01-01", "orders": 50}
    ],
    "payment_method_distribution": [
      {"label": "UPI", "count": 30, "amount": 15000.00},
      {"label": "CASH", "count": 15, "amount": 7500.00}
    ],
    "revenue_by_order_source": [
      {"label": "PRESCRIPTION", "revenue": 30000.00},
      {"label": "OTC", "revenue": 20000.00}
    ]
  }
}
```

**KPIs Included:**
- Total revenue (all-time)
- Today's revenue
- Monthly and yearly revenue
- Total orders and order counts by period
- Average order value (AOV)
- Revenue growth rate
- Payment success rate
- Outstanding payments

**Alerts:**
- `LOW_REVENUE` - Revenue below average
- `HIGH_OUTSTANDING` - High outstanding payments
- `PAYMENT_FAILURE` - Payment failures detected

**Charts:**
- Revenue trends over time
- Orders trends
- Revenue vs orders comparison
- Payment method distribution
- Revenue by payment method
- Daily revenue comparison
- Monthly revenue trend
- Order status distribution
- Revenue by order source
- Average order value trend
- Revenue growth rate
- Payment status breakdown

#### 2. Inventory Dashboard
**Base Path:** `/api/v1/dashboards/inventory`

##### Get Inventory Dashboard
**GET** `/api/v1/dashboards/inventory/`

Retrieves inventory analytics including stock levels, expiry tracking, and stock movements.

**Query Parameters:**
- `period` (string, default: "30d"): Time period - `30d`, `3m`, `1y`
- `include_charts` (boolean, default: true): Include chart data in response
- `low_stock_threshold` (int, default: 10, min: 1): Low stock threshold for alerts
- `expiry_days` (int, default: 30, min: 1): Days ahead for expiring soon alerts
- `top_products_limit` (int, default: 10, range: 1-50): Number of top products to return
- `expiry_months` (int, default: 6, range: 1-24): Months for expiry timeline

**Response:** 200 OK
```json
{
  "kpis": {
    "total_stock_value": 1250000.00,
    "total_stock_quantity": 5000,
    "total_active_products": 150,
    "total_batches": 200,
    "low_stock_count": 15,
    "out_of_stock_count": 5,
    "expiring_soon_count": 8,
    "expired_count": 2,
    "stock_turnover_rate": 2.5,
    "average_stock_value": 8333.33
  },
  "alerts": [
    {
      "type": "LOW_STOCK",
      "severity": "WARNING",
      "message": "Crocin is running low (5 units remaining)",
      "medicine_brand_id": "uuid",
      "medicine_brand_name": "Crocin",
      "current_quantity": 5,
      "threshold": 10
    },
    {
      "type": "EXPIRING_SOON",
      "severity": "WARNING",
      "message": "Batch BATCH-0925 expires in 15 days",
      "batch_id": "uuid",
      "batch_number": "BATCH-0925",
      "expiry_date": "2026-02-15"
    }
  ],
  "charts": {
    "stock_value_trend": [
      {"date": "2026-01-01", "value": 1200000.00}
    ],
    "stock_by_category": [
      {"label": "Antibiotic", "value": 300000.00, "quantity": 1200}
    ],
    "top_products": [
      {"label": "Crocin", "value": 50000.00, "quantity": 200}
    ],
    "expiry_timeline": [
      {"date": "2026-02-01", "count": 5}
    ]
  }
}
```

**KPIs Included:**
- Total stock value and quantity
- Active products and batches count
- Low stock and out of stock counts
- Expiring soon and expired counts
- Stock turnover rate
- Average stock value per product

**Alerts:**
- `LOW_STOCK` - Products below threshold
- `OUT_OF_STOCK` - Products with zero stock
- `EXPIRING_SOON` - Batches expiring within specified days
- `EXPIRED` - Expired batches

**Charts:**
- Stock value trend over time
- Stock by category
- Top products by stock value
- Stock distribution (low/normal/out)
- Expiry timeline
- Stock movement trend
- Stock by dosage form

#### 3. Orders Dashboard
**Base Path:** `/api/v1/dashboards/orders`

##### Get Orders Dashboard
**GET** `/api/v1/dashboards/orders/`

Retrieves order analytics including order counts, status distribution, and processing times.

**Query Parameters:**
- `period` (string, default: "month"): KPI period - `today`, `week`, `month`, `quarter`, `year`
- `include_charts` (boolean, default: true): Include chart data in response
- `trend_days` (int, default: 30, range: 1-365): Days for trend charts

**Response:** 200 OK
```json
{
  "kpis": {
    "total_orders": 5000,
    "today_orders": 50,
    "month_orders": 1500,
    "pending_orders": 25,
    "approval_pending": 10,
    "completed_orders": 4500,
    "cancelled_orders": 50,
    "average_processing_time_hours": 2.5,
    "fulfillment_rate": 90.0
  },
  "alerts": [
    {
      "type": "HIGH_PENDING",
      "severity": "WARNING",
      "message": "25 pending orders exceed threshold of 20",
      "pending_count": 25,
      "threshold": 20
    }
  ],
  "charts": {
    "orders_over_time": [
      {"date": "2026-01-01", "orders": 50}
    ],
    "order_status_distribution": [
      {"label": "COMPLETED", "count": 4500},
      {"label": "PENDING", "count": 25}
    ],
    "orders_by_source": [
      {"label": "PRESCRIPTION", "count": 30},
      {"label": "OTC", "count": 20}
    ],
    "processing_time_analysis": [
      {"date": "2026-01-01", "average_time": 2.5}
    ]
  }
}
```

**KPIs Included:**
- Total orders (all-time)
- Today's and monthly orders
- Pending orders count
- Approval pending count
- Completed and cancelled orders
- Average processing time (hours)
- Fulfillment rate (%)

**Alerts:**
- `HIGH_PENDING` - High number of pending orders
- `LONG_PROCESSING` - Long average processing times
- `HIGH_CANCELLATION` - High cancellation rate

**Charts:**
- Orders over time
- Order status distribution
- Orders by source
- Processing time analysis

#### 4. Sales Dashboard
**Base Path:** `/api/v1/dashboards/sales`

##### Get Sales Dashboard
**GET** `/api/v1/dashboards/sales/`

Retrieves sales analytics including top products, sales trends, and category breakdowns.

**Query Parameters:**
- `period` (string, default: "30d"): Time period - `30d`, `3m`, `1y`
- `include_charts` (boolean, default: true): Include chart data in response
- `top_products_limit` (int, default: 10, range: 1-50): Number of top products to return

**Response:** 200 OK
```json
{
  "kpis": {
    "total_sales_quantity": 10000,
    "top_selling_product": "Crocin",
    "sales_growth_rate": 12.5,
    "average_sales_per_day": 333.33,
    "customer_count": 500
  },
  "charts": {
    "top_products": [
      {"label": "Crocin", "quantity": 500, "revenue": 12500.00}
    ],
    "sales_by_category": [
      {"label": "Antibiotic", "quantity": 2000, "revenue": 50000.00}
    ],
    "sales_trend": [
      {"date": "2026-01-01", "quantity": 333, "revenue": 8325.00}
    ],
    "sales_by_dosage_form": [
      {"label": "Tablet", "quantity": 6000, "count": 3000}
    ]
  }
}
```

**KPIs Included:**
- Total sales quantity
- Top selling product name
- Sales growth rate (%)
- Average sales per day
- Unique customer count

**Charts:**
- Top selling products
- Sales by category
- Sales trend over time
- Sales by dosage form

---

## 15. Razorpay Payment Gateway

**Base Path:** `/api/v1/razorpay`

### Purpose

Razorpay powers online payments for customer orders: create order, open Razorpay Checkout (UPI, cards, net banking), verify signature, and optionally process refunds. All flows require a valid JWT (customer for initiate/verify/status; staff with `PAYMENT_PROCESS` for refund).

### Environment

Set in `.env`:

- `RAZORPAY_KEY_ID` – Public key (used by frontend checkout).
- `RAZORPAY_KEY_SECRET` – Secret key (server-side only; never expose to frontend).

Get both from [Razorpay Dashboard](https://dashboard.razorpay.com) (use test keys for development).

### Endpoints

#### Initiate Payment (create order + Razorpay order)

**POST** `/api/v1/razorpay/initiate`

Creates the order, order items, and payment record, then creates a Razorpay order. Returns data needed for the frontend to open Razorpay Checkout.

**Headers:** `Authorization: Bearer <access_token>` (customer JWT)

**Request Body:**
```json
{
  "customer_name": "John Doe",
  "customer_phone": "9876543210",
  "customer_email": "john@example.com",
  "delivery_address": "123 Street, City, State - 560001",
  "pincode": "560001",
  "city": "Bangalore",
  "items": [
    {
      "medicine_brand_id": "uuid",
      "name": "Crocin 500mg",
      "quantity": 2,
      "price": 25.50,
      "requires_prescription": false
    }
  ],
  "subtotal": 51.00,
  "delivery_fee": 40.00,
  "discount_amount": 0,
  "final_amount": 91.00,
  "coupon_code": null,
  "prescription_id": null
}
```

**Response:** 200 OK
```json
{
  "order_id": "uuid-of-our-order",
  "razorpay_order_id": "order_xxxx",
  "key_id": "rzp_test_xxxx",
  "amount": 9100
}
```

`amount` is in **paise** (₹1 = 100 paise). Frontend uses `key_id`, `razorpay_order_id`, and `amount` with [Razorpay Checkout](https://razorpay.com/docs/payments/payment-gateway/web-integration/checkout/).

#### Verify Payment (after checkout success)

**POST** `/api/v1/razorpay/verify`

Verifies the Razorpay signature and updates order and payment status. Call this from the frontend after the user completes payment in Razorpay Checkout.

**Headers:** `Authorization: Bearer <access_token>` (customer JWT)

**Request Body:**
```json
{
  "razorpay_payment_id": "pay_xxxx",
  "razorpay_order_id": "order_xxxx",
  "razorpay_signature": "signature_from_checkout"
}
```

**Response:** 200 OK
```json
{
  "order_id": "uuid",
  "payment_status": "SUCCESS",
  "amount": 91.00,
  "transaction_id": "pay_xxxx",
  "order_status": "CONFIRMED"
}
```

#### Get Payment Status

**GET** `/api/v1/razorpay/status/{order_id}`

Returns current payment and order status for the given order (e.g. for callback page or polling). Caller must own the order.

**Headers:** `Authorization: Bearer <access_token>`

**Response:** 200 OK
```json
{
  "order_id": "uuid",
  "payment_status": "SUCCESS",
  "amount": 91.00,
  "transaction_id": "pay_xxxx",
  "order_status": "CONFIRMED"
}
```

#### Refund Payment (admin)

**POST** `/api/v1/razorpay/refund/{order_id}`

Initiates a full or partial refund for a paid order. Requires `PAYMENT_PROCESS` permission.

**Headers:** `Authorization: Bearer <access_token>` (staff JWT)

**Request Body:**
```json
{
  "amount": 50.00,
  "reason": "Customer request"
}
```

Omit `amount` for full refund.

**Response:** 200 OK
```json
{
  "order_id": "uuid",
  "refund_status": "COMPLETED",
  "refund_amount": 50.00,
  "refund_transaction_id": "rfnd_xxxx"
}
```

---

## Common Features

### Pagination

All list endpoints support pagination:

```
GET /api/v1/roles/?limit=20&offset=0
```

**Response:**
```json
{
  "items": [...],
  "pagination": {
    "total": 100,
    "limit": 20,
    "offset": 0,
    "has_next": true,
    "has_previous": false
  }
}
```

### Search

Search across multiple fields (case-insensitive):

```
GET /api/v1/roles/?search=PHARMACIST
```

Searches in: `name`, `description` (and other searchable fields)

### Sorting

Sort by any field in ascending or descending order:

```
GET /api/v1/roles/?sort_by=name&sort_order=asc
```

### Audit Fields

All records automatically include:
- `id` - UUID (auto-generated)
- `created_by` - User who created (from JWT token)
- `created_at` - Creation timestamp (IST timezone)
- `created_ip` - IP address of creator
- `updated_by` - User who last updated
- `updated_at` - Last update timestamp
- `updated_ip` - IP address of updater
- `is_deleted` - Soft delete flag

**Note:** `is_active` is automatically set to `true` for master tables during creation.

---

## Error Handling

### Standard Error Response

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

- `200 OK` - Successful GET, PATCH, DELETE
- `201 Created` - Successful POST (create)
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict (e.g., duplicate)
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

### Example Error Responses

**404 Not Found:**
```json
{
  "detail": "Role with ID b1f9e123-4567-8901-2345-678901234567 not found"
}
```

**422 Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Health Check Endpoints

### Root Endpoint
**GET** `/`

Returns API information.

**Response:**
```json
{
  "message": "Medical Shop Pharmacy API",
  "status": "healthy"
}
```

### Health Check
**GET** `/health`

Returns API and database connection status.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

---

## API Documentation

### Interactive Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### OpenAPI Schema

**GET** `/openapi.json`

Returns the OpenAPI 3.0 schema for the API.

---

## Notes

1. **Automatic Fields:** `id`, `created_at`, `created_by`, `created_ip`, `is_active` (for master tables), and `is_deleted` are automatically set by the backend and should not be included in create requests.

2. **Update Requests:** All fields in update requests are optional. Only provided fields will be updated.

3. **Soft Delete:** Delete operations are soft deletes (sets `is_deleted = true`). Records are not physically removed from the database.

4. **Timezone:** All timestamps are in IST (Indian Standard Time, UTC+5:30).

5. **Authentication:** The API uses JWT (access and refresh tokens). Login via `/api/v1/auth/login`; include `Authorization: Bearer <access_token>` for protected endpoints. Razorpay endpoints require a valid customer or staff JWT as described in [§15 Razorpay](#15-razorpay-payment-gateway).

6. **IP Address:** Client IP addresses are automatically captured from request headers for audit purposes.

---

## Support

For issues or questions, please refer to the API documentation at `/docs` or contact the development team.
