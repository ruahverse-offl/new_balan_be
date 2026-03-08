# Dashboard Implementation Plan

## Overview

This document outlines the dashboard requirements for the Medical Shop Pharmacy Management System. Dashboards provide real-time insights, KPIs, alerts, and visualizations to help manage inventory, finances, orders, and operations.

---

## 1. Products/Inventory Dashboard

**Purpose:** Monitor stock levels, track inventory value, manage expiry dates, and get alerts for low stock or expiring medicines.

### 1.1 Key Performance Indicators (KPIs)

#### Stock Overview KPIs
- **Total Stock Value** (₹)
  - Sum of: `SUM(product_batches.quantity_available * product_batches.purchase_price)`
  - Shows total investment in inventory
  
- **Total Stock Quantity** (units)
  - Sum of: `SUM(product_batches.quantity_available)`
  - Total number of medicine units in stock

- **Total Active Products**
  - Count of distinct `medicine_brands` with `quantity_available > 0`
  - Number of different products currently in stock

- **Total Batches**
  - Count of `product_batches` with `quantity_available > 0`
  - Number of active batches

#### Low Stock Alerts KPI
- **Low Stock Items Count**
  - Count of medicines where `quantity_available <= low_stock_threshold`
  - Default threshold: 10 units (configurable)
  - Query: `COUNT(*) WHERE quantity_available <= threshold`

- **Out of Stock Items Count**
  - Count of medicines where `quantity_available = 0`
  - Critical items that need immediate restocking

#### Expiry Alerts KPI
- **Expiring Soon Count** (within 30 days)
  - Count of batches where `expiry_date <= CURRENT_DATE + 30 days`
  - Items that need to be sold or returned soon

- **Expired Items Count**
  - Count of batches where `expiry_date < CURRENT_DATE`
  - Items that should be removed from sale

#### Stock Movement KPI
- **Stock Turnover Rate**
  - `Total Sales Quantity / Average Stock Quantity`
  - Measures how quickly inventory is sold

- **Average Stock Value**
  - `Total Stock Value / Total Active Products`
  - Average investment per product

### 1.2 Alerts

#### Low Stock Alert
- **Trigger:** `quantity_available <= low_stock_threshold`
- **Severity:** Warning (Yellow)
- **Data:** Medicine brand name, current quantity, threshold, days until out of stock
- **Action:** Generate purchase order suggestion

#### Out of Stock Alert
- **Trigger:** `quantity_available = 0`
- **Severity:** Critical (Red)
- **Data:** Medicine brand name, last sold date, average monthly sales
- **Action:** Urgent restocking required

#### Expiring Soon Alert
- **Trigger:** `expiry_date <= CURRENT_DATE + 30 days AND expiry_date > CURRENT_DATE`
- **Severity:** Warning (Yellow)
- **Data:** Batch number, medicine brand, expiry date, quantity available
- **Action:** Priority sales or return to supplier

#### Expired Alert
- **Trigger:** `expiry_date < CURRENT_DATE AND quantity_available > 0`
- **Severity:** Critical (Red)
- **Data:** Batch number, medicine brand, expiry date, quantity
- **Action:** Remove from sale, mark for disposal

### 1.3 Graphs/Charts

#### 1. Stock Value Over Time (Line Chart)
- **X-axis:** Date (last 30 days, 3 months, 6 months, 1 year)
- **Y-axis:** Stock Value (₹)
- **Data:** Daily aggregation of total stock value
- **Purpose:** Track inventory investment trends

#### 2. Stock Levels by Category (Bar Chart)
- **X-axis:** Therapeutic Category (Antibiotic, Pain Reliever, etc.)
- **Y-axis:** Total Quantity or Stock Value
- **Data:** Group by `therapeutic_categories.name`
- **Purpose:** See which categories have most inventory

#### 3. Top 10 Products by Stock Value (Horizontal Bar Chart)
- **X-axis:** Stock Value (₹)
- **Y-axis:** Medicine Brand Name
- **Data:** Top 10 `medicine_brands` by `SUM(quantity_available * purchase_price)`
- **Purpose:** Identify high-value inventory items

#### 4. Low Stock vs Normal Stock (Pie Chart)
- **Segments:** Low Stock, Normal Stock, Out of Stock
- **Data:** Count of products in each category
- **Purpose:** Quick overview of stock health

#### 5. Expiry Timeline (Timeline/Bar Chart)
- **X-axis:** Months (next 6 months)
- **Y-axis:** Number of batches expiring
- **Data:** Group batches by expiry month
- **Purpose:** Plan for upcoming expiries

#### 6. Stock Movement Trend (Line Chart)
- **X-axis:** Date
- **Y-axis:** Quantity Change
- **Data:** Daily aggregation from `inventory_transactions`
- **Purpose:** Track stock additions and sales

#### 7. Stock by Dosage Form (Donut Chart)
- **Segments:** Tablet, Capsule, Syrup, Injection, etc.
- **Data:** Count or value by `medicines.dosage_form`
- **Purpose:** Understand product mix

#### 8. Fast Moving vs Slow Moving (Scatter Plot)
- **X-axis:** Stock Turnover Rate
- **Y-axis:** Stock Value
- **Data:** Each point is a medicine brand
- **Purpose:** Identify products that need attention

### 1.4 API Endpoints

**Single Consolidated Endpoint:**

```
GET /api/v1/dashboards/inventory
```

**Query Parameters:**
- `period` (optional): `30d`, `3m`, `6m`, `1y` - Time period for trend data (default: `30d`)
- `include_charts` (optional): `true`, `false` - Include chart data (default: `true`)
- `low_stock_threshold` (optional): Integer - Threshold for low stock alerts (default: `10`)
- `expiry_days` (optional): Integer - Days ahead for expiring soon alerts (default: `30`)
- `top_products_limit` (optional): Integer - Number of top products to return (default: `10`)

**Response Structure:**
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
      "type": "OUT_OF_STOCK",
      "severity": "CRITICAL",
      "message": "Calpol is out of stock",
      "medicine_brand_id": "uuid",
      "medicine_brand_name": "Calpol",
      "current_quantity": 0
    },
    {
      "type": "EXPIRING_SOON",
      "severity": "WARNING",
      "message": "Batch BATCH-0925 expires in 15 days",
      "batch_id": "uuid",
      "batch_number": "BATCH-0925",
      "medicine_brand_name": "Paracetamol",
      "expiry_date": "2026-02-15",
      "quantity_available": 50
    },
    {
      "type": "EXPIRED",
      "severity": "CRITICAL",
      "message": "Batch BATCH-0824 has expired",
      "batch_id": "uuid",
      "batch_number": "BATCH-0824",
      "medicine_brand_name": "Amoxicillin",
      "expiry_date": "2026-01-15",
      "quantity_available": 20
    }
  ],
  "charts": {
    "stock_value_trend": {
      "type": "line",
      "data": [
        {"date": "2026-01-01", "value": 1200000.00},
        {"date": "2026-01-02", "value": 1250000.00}
      ]
    },
    "stock_by_category": {
      "type": "bar",
      "data": [
        {"category": "Antibiotic", "quantity": 1000, "value": 250000.00},
        {"category": "Pain Reliever", "quantity": 800, "value": 200000.00}
      ]
    },
    "top_products": {
      "type": "horizontal_bar",
      "data": [
        {"medicine_brand": "Crocin", "value": 50000.00},
        {"medicine_brand": "Calpol", "value": 45000.00}
      ]
    },
    "stock_distribution": {
      "type": "pie",
      "data": [
        {"label": "Low Stock", "count": 15},
        {"label": "Normal Stock", "count": 130},
        {"label": "Out of Stock", "count": 5}
      ]
    },
    "expiry_timeline": {
      "type": "bar",
      "data": [
        {"month": "2026-02", "batch_count": 5},
        {"month": "2026-03", "batch_count": 8}
      ]
    },
    "stock_movement": {
      "type": "line",
      "data": [
        {"date": "2026-01-01", "quantity_change": 100},
        {"date": "2026-01-02", "quantity_change": -50}
      ]
    },
    "stock_by_dosage_form": {
      "type": "donut",
      "data": [
        {"dosage_form": "Tablet", "count": 80},
        {"dosage_form": "Capsule", "count": 50}
      ]
    }
  }
}
```

**Benefits:**
- Single API call gets all dashboard data
- Reduces network overhead
- Frontend can cache entire response
- Easier to implement lazy loading of charts
- Better performance with parallel database queries

---

## 2. Finance Dashboard

**Purpose:** Track revenue, payments, orders, and financial performance metrics.

### 2.1 Key Performance Indicators (KPIs)

#### Revenue KPIs
- **Total Revenue** (₹)
  - Sum of: `SUM(payments.amount WHERE payment_status = 'COMPLETED')`
  - All-time total revenue

- **Today's Revenue** (₹)
  - Sum of: `SUM(payments.amount WHERE DATE(created_at) = TODAY AND payment_status = 'COMPLETED')`
  - Daily revenue tracking

- **This Month's Revenue** (₹)
  - Sum of: `SUM(payments.amount WHERE MONTH(created_at) = CURRENT_MONTH AND payment_status = 'COMPLETED')`
  - Monthly revenue tracking

- **This Year's Revenue** (₹)
  - Sum of: `SUM(payments.amount WHERE YEAR(created_at) = CURRENT_YEAR AND payment_status = 'COMPLETED')`
  - Yearly revenue tracking

#### Order KPIs
- **Total Orders**
  - Count of: `COUNT(orders WHERE is_deleted = false)`
  - All-time order count

- **Today's Orders**
  - Count of: `COUNT(orders WHERE DATE(created_at) = TODAY)`
  - Daily order count

- **This Month's Orders**
  - Count of: `COUNT(orders WHERE MONTH(created_at) = CURRENT_MONTH)`
  - Monthly order count

- **Pending Orders**
  - Count of: `COUNT(orders WHERE order_status = 'PENDING')`
  - Orders awaiting processing

- **Completed Orders**
  - Count of: `COUNT(orders WHERE order_status = 'COMPLETED')`
  - Successfully fulfilled orders

#### Financial Metrics KPIs
- **Average Order Value (AOV)** (₹)
  - `Total Revenue / Total Orders`
  - Average amount per order

- **Revenue Growth Rate** (%)
  - `((This Month Revenue - Last Month Revenue) / Last Month Revenue) * 100`
  - Month-over-month growth

- **Payment Success Rate** (%)
  - `(COMPLETED payments / TOTAL payments) * 100`
  - Percentage of successful payments

- **Outstanding Payments** (₹)
  - Sum of: `SUM(payments.amount WHERE payment_status = 'PENDING')`
  - Unpaid orders amount

### 2.2 Alerts

#### Low Revenue Alert
- **Trigger:** `Today's Revenue < (Average Daily Revenue * 0.7)`
- **Severity:** Warning (Yellow)
- **Data:** Today's revenue, average daily revenue, percentage below average
- **Action:** Review sales activities

#### High Outstanding Payments Alert
- **Trigger:** `Outstanding Payments > (Monthly Revenue * 0.2)`
- **Severity:** Warning (Yellow)
- **Data:** Outstanding amount, number of pending payments
- **Action:** Follow up on pending payments

#### Payment Failure Alert
- **Trigger:** `Payment failure rate > 10% in last 24 hours`
- **Severity:** Warning (Yellow)
- **Data:** Failed payment count, failure rate
- **Action:** Investigate payment gateway issues

### 2.3 Graphs/Charts

#### 1. Revenue Over Time (Line Chart)
- **X-axis:** Date (Daily, Weekly, Monthly views)
- **Y-axis:** Revenue (₹)
- **Data:** Daily/weekly/monthly aggregation of completed payments
- **Purpose:** Track revenue trends and growth

#### 2. Orders Over Time (Line Chart)
- **X-axis:** Date
- **Y-axis:** Number of Orders
- **Data:** Daily aggregation of orders
- **Purpose:** Track order volume trends

#### 3. Revenue vs Orders (Dual-Axis Line Chart)
- **X-axis:** Date
- **Y-axis (Left):** Revenue (₹)
- **Y-axis (Right):** Number of Orders
- **Data:** Combined revenue and order data
- **Purpose:** Compare revenue and order trends

#### 4. Payment Method Distribution (Pie/Donut Chart)
- **Segments:** Cash, UPI, Card, Wallet, Net Banking
- **Data:** Count or amount by `payments.payment_method`
- **Purpose:** Understand payment preferences

#### 5. Revenue by Payment Method (Bar Chart)
- **X-axis:** Payment Method
- **Y-axis:** Revenue (₹)
- **Data:** Sum of amounts grouped by payment method
- **Purpose:** See which payment methods generate most revenue

#### 6. Daily Revenue Comparison (Bar Chart)
- **X-axis:** Day of Week (Monday-Sunday)
- **Y-axis:** Average Revenue (₹)
- **Data:** Average revenue per day of week
- **Purpose:** Identify peak sales days

#### 7. Monthly Revenue Trend (Bar Chart)
- **X-axis:** Month (Last 12 months)
- **Y-axis:** Revenue (₹)
- **Data:** Monthly aggregation
- **Purpose:** Track monthly performance

#### 8. Order Status Distribution (Pie Chart)
- **Segments:** Pending, Approved, Dispensed, Completed, Cancelled
- **Data:** Count of orders by status
- **Purpose:** Understand order fulfillment status

#### 9. Revenue by Order Source (Bar Chart)
- **X-axis:** Order Source (PRESCRIPTION, OTC, WALK_IN, ONLINE)
- **Y-axis:** Revenue (₹)
- **Data:** Sum of revenue grouped by order source
- **Purpose:** Identify most profitable order channels

#### 10. Average Order Value Trend (Line Chart)
- **X-axis:** Date
- **Y-axis:** Average Order Value (₹)
- **Data:** Daily/weekly AOV calculation
- **Purpose:** Track if customers are spending more per order

#### 11. Revenue Growth Rate (Line Chart)
- **X-axis:** Month
- **Y-axis:** Growth Rate (%)
- **Data:** Month-over-month percentage change
- **Purpose:** Monitor business growth

#### 12. Payment Status Breakdown (Stacked Bar Chart)
- **X-axis:** Date
- **Y-axis:** Payment Count
- **Stacks:** Completed, Pending, Failed, Refunded
- **Data:** Daily aggregation by payment status
- **Purpose:** Track payment processing health

### 2.4 API Endpoints

**Single Consolidated Endpoint:**

```
GET /api/v1/dashboards/finance
```

**Query Parameters:**
- `period` (optional): `today`, `week`, `month`, `quarter`, `year`, `all` - Time period for KPIs (default: `month`)
- `trend_period` (optional): `7d`, `30d`, `3m`, `6m`, `1y` - Time period for trend graphs (default: `30d`)
- `trend_granularity` (optional): `daily`, `weekly`, `monthly` - Granularity for trend data (default: `daily`)
- `include_charts` (optional): `true`, `false` - Include chart data (default: `true`)
- `monthly_trend_months` (optional): Integer - Number of months for monthly trend (default: `12`)

**Response Structure:**
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
      "message": "Today's revenue is 30% below average",
      "today_revenue": 50000.00,
      "average_daily_revenue": 71428.57,
      "percentage_below": 30.0
    },
    {
      "type": "HIGH_OUTSTANDING",
      "severity": "WARNING",
      "message": "Outstanding payments exceed 20% of monthly revenue",
      "outstanding_amount": 25000.00,
      "monthly_revenue": 1500000.00,
      "percentage": 1.67
    }
  ],
  "charts": {
    "revenue_trend": {
      "type": "line",
      "granularity": "daily",
      "data": [
        {"date": "2026-01-01", "revenue": 45000.00},
        {"date": "2026-01-02", "revenue": 50000.00}
      ]
    },
    "orders_trend": {
      "type": "line",
      "granularity": "daily",
      "data": [
        {"date": "2026-01-01", "orders": 45},
        {"date": "2026-01-02", "orders": 50}
      ]
    },
    "revenue_vs_orders": {
      "type": "dual_axis_line",
      "data": [
        {
          "date": "2026-01-01",
          "revenue": 45000.00,
          "orders": 45
        }
      ]
    },
    "payment_method_distribution": {
      "type": "pie",
      "data": [
        {"method": "UPI", "count": 2000, "amount": 2000000.00},
        {"method": "CASH", "count": 1500, "amount": 1500000.00},
        {"method": "CARD", "count": 1000, "amount": 1000000.00}
      ]
    },
    "revenue_by_payment_method": {
      "type": "bar",
      "data": [
        {"method": "UPI", "revenue": 2000000.00},
        {"method": "CASH", "revenue": 1500000.00}
      ]
    },
    "daily_revenue_comparison": {
      "type": "bar",
      "data": [
        {"day": "Monday", "average_revenue": 60000.00},
        {"day": "Tuesday", "average_revenue": 65000.00}
      ]
    },
    "monthly_revenue_trend": {
      "type": "bar",
      "data": [
        {"month": "2025-02", "revenue": 1300000.00},
        {"month": "2025-03", "revenue": 1500000.00}
      ]
    },
    "order_status_distribution": {
      "type": "pie",
      "data": [
        {"status": "COMPLETED", "count": 4500},
        {"status": "PENDING", "count": 25}
      ]
    },
    "revenue_by_order_source": {
      "type": "bar",
      "data": [
        {"source": "PRESCRIPTION", "revenue": 2000000.00},
        {"source": "OTC", "revenue": 1500000.00}
      ]
    },
    "aov_trend": {
      "type": "line",
      "data": [
        {"date": "2026-01-01", "aov": 1000.00},
        {"date": "2026-01-02", "aov": 1111.11}
      ]
    },
    "revenue_growth_rate": {
      "type": "line",
      "data": [
        {"month": "2025-02", "growth_rate": 10.5},
        {"month": "2025-03", "growth_rate": 15.5}
      ]
    },
    "payment_status_breakdown": {
      "type": "stacked_bar",
      "data": [
        {
          "date": "2026-01-01",
          "completed": 45,
          "pending": 3,
          "failed": 1,
          "refunded": 0
        }
      ]
    }
  }
}
```

**Benefits:**
- Single API call for all finance dashboard data
- Reduces server load and network overhead
- Frontend can render all charts from one response
- Better caching strategy
- Parallel database queries for better performance

---

## 3. Orders Dashboard

**Purpose:** Monitor order processing, track order status, and manage order fulfillment.

### 3.1 Key Performance Indicators (KPIs)

- **Total Orders** - All-time order count
- **Today's Orders** - Orders created today
- **Pending Orders** - Orders awaiting processing
- **Approval Pending** - Orders awaiting pharmacist approval
- **Completed Orders** - Successfully fulfilled orders
- **Cancelled Orders** - Cancelled order count
- **Average Processing Time** - Average time from creation to completion
- **Order Fulfillment Rate** - Percentage of orders completed

### 3.2 Alerts

- **High Pending Orders** - More than 20 pending orders
- **Long Processing Time** - Orders pending for more than 24 hours
- **High Cancellation Rate** - More than 10% cancellation rate

### 3.3 Graphs/Charts

1. **Orders Over Time** - Daily/weekly order volume
2. **Order Status Distribution** - Pie chart of order statuses
3. **Orders by Source** - Bar chart (PRESCRIPTION, OTC, etc.)
4. **Order Processing Time** - Average time by status
5. **Orders by Day of Week** - Peak order days
6. **Cancellation Rate Trend** - Line chart over time

### 3.4 API Endpoints

**Single Consolidated Endpoint:**

```
GET /api/v1/dashboards/orders
```

**Query Parameters:**
- `period` (optional): `today`, `week`, `month`, `quarter`, `year` - Time period (default: `month`)
- `include_charts` (optional): `true`, `false` - Include chart data (default: `true`)

**Response Structure:**
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
      "message": "25 orders are pending (above threshold of 20)",
      "pending_count": 25,
      "threshold": 20
    }
  ],
  "charts": {
    "orders_over_time": {...},
    "order_status_distribution": {...},
    "orders_by_source": {...},
    "processing_time_analysis": {...}
  }
}
```

---

## 4. Sales Dashboard

**Purpose:** Analyze sales performance, top-selling products, and customer behavior.

### 4.1 Key Performance Indicators (KPIs)

- **Total Sales Quantity** - Units sold
- **Top Selling Product** - Best-selling medicine brand
- **Sales Growth Rate** - Month-over-month growth
- **Average Sales per Day** - Daily average sales
- **Customer Count** - Unique customers

### 4.2 Graphs/Charts

1. **Top 10 Selling Products** - Horizontal bar chart
2. **Sales by Category** - Bar chart by therapeutic category
3. **Sales Trend** - Line chart over time
4. **Sales by Dosage Form** - Pie chart
5. **Customer Purchase Frequency** - Histogram
6. **Sales Heatmap** - Day of week vs Hour of day

### 4.3 API Endpoints

**Single Consolidated Endpoint:**

```
GET /api/v1/dashboards/sales
```

**Query Parameters:**
- `period` (optional): `7d`, `30d`, `3m`, `6m`, `1y` - Time period (default: `30d`)
- `top_products_limit` (optional): Integer - Number of top products (default: `10`)
- `include_charts` (optional): `true`, `false` - Include chart data (default: `true`)

**Response Structure:**
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
    "top_products": {...},
    "sales_by_category": {...},
    "sales_trend": {...},
    "sales_by_dosage_form": {...}
  }
}
```

---

## 5. Implementation Plan

### Phase 1: Infrastructure Setup
1. Create dashboard router structure (`app/routes/dashboards/`)
2. Create dashboard service layer (`app/services/dashboards/`)
3. Create dashboard repository layer with aggregation queries (`app/repositories/dashboards/`)
4. Create dashboard schemas (response models) (`app/schemas/dashboards/`)
5. Set up database connection pooling for parallel queries

### Phase 2: Products/Inventory Dashboard
1. Create `GET /api/v1/dashboards/inventory` endpoint
2. Implement KPIs calculation (parallel queries)
3. Implement alerts generation
4. Implement all chart data aggregations
5. Optimize queries with proper indexes
6. Add response caching (5-10 minutes)

### Phase 3: Finance Dashboard
1. Create `GET /api/v1/dashboards/finance` endpoint
2. Implement KPIs calculation (parallel queries)
3. Implement alerts generation
4. Implement all chart data aggregations
5. Optimize queries with proper indexes
6. Add response caching (5-10 minutes)

### Phase 4: Orders Dashboard
1. Create `GET /api/v1/dashboards/orders` endpoint
2. Implement KPIs and charts
3. Add caching

### Phase 5: Sales Dashboard
1. Create `GET /api/v1/dashboards/sales` endpoint
2. Implement KPIs and charts
3. Add caching

### Phase 6: Testing & Optimization
1. Write unit tests for dashboard services
2. Write integration tests for dashboard endpoints
3. Performance testing with load testing tools
4. Optimize slow queries
5. Add database indexes
6. Implement Redis caching for dashboard responses
7. Add query result pagination for large datasets

---

## 6. Technical Considerations

### 6.1 Database Queries
- Use SQL aggregations (`SUM`, `COUNT`, `AVG`, `GROUP BY`)
- Use window functions for trends and comparisons
- Use date functions for time-based filtering
- Consider materialized views for complex aggregations

### 6.2 Performance Optimization
- Add database indexes on frequently queried columns:
  - `product_batches.expiry_date`
  - `product_batches.quantity_available`
  - `payments.created_at`
  - `payments.payment_status`
  - `orders.created_at`
  - `orders.order_status`
  - `inventory_transactions.created_at`

### 6.3 Caching Strategy
- **Single Endpoint Caching:** Cache entire dashboard response for 5-10 minutes
- **Cache Key:** `dashboard:{module}:{period}:{params_hash}`
- **Invalidation:** Invalidate on data updates (orders, payments, inventory changes)
- **Cache Storage:** Redis (preferred) or in-memory cache
- **Cache Benefits:**
  - Reduces database load significantly
  - Faster response times
  - Better user experience
  - Single cache entry per dashboard instead of multiple

### 6.4 Date Range Parameters
- Support common periods: `today`, `week`, `month`, `quarter`, `year`, `custom`
- Support custom date ranges: `start_date` and `end_date`
- Default to last 30 days for trend graphs

### 6.5 Response Format
```json
{
  "kpis": {
    "total_stock_value": 1250000.00,
    "low_stock_count": 15,
    "expiring_soon_count": 8
  },
  "alerts": [
    {
      "type": "LOW_STOCK",
      "severity": "WARNING",
      "message": "Crocin is running low (5 units remaining)",
      "medicine_brand_id": "uuid",
      "current_quantity": 5,
      "threshold": 10
    }
  ],
  "charts": {
    "stock_value_trend": {
      "data": [
        {"date": "2026-01-01", "value": 1200000.00},
        {"date": "2026-01-02", "value": 1250000.00}
      ]
    }
  }
}
```

---

## 7. Future Enhancements

1. **Real-time Updates** - WebSocket support for live dashboard updates
2. **Export Functionality** - PDF/Excel export of dashboard data
3. **Custom Dashboards** - User-configurable dashboard layouts
4. **Email Alerts** - Automated email notifications for critical alerts
5. **Mobile Dashboard** - Optimized dashboard for mobile devices
6. **Predictive Analytics** - Forecast future sales and inventory needs
7. **Comparative Analysis** - Compare current period with previous period
8. **Drill-down Functionality** - Click on charts to see detailed data

---

## 8. Priority Order

### High Priority (Phase 1-2)
1. Products/Inventory Dashboard - KPIs and Low Stock Alerts
2. Finance Dashboard - Revenue and Orders KPIs

### Medium Priority (Phase 3-4)
3. Finance Dashboard - All graphs
4. Orders Dashboard - Basic KPIs and status distribution

### Low Priority (Phase 5-6)
5. Sales Dashboard
6. Advanced analytics and predictions

---

## Notes

### Single Endpoint Benefits
- **Reduced API Calls:** Frontend makes 1 call instead of 10+ calls
- **Better Performance:** Parallel database queries execute faster
- **Easier Caching:** Single cache entry per dashboard
- **Simpler Frontend:** One response handler instead of multiple
- **Reduced Server Load:** Fewer HTTP requests = less overhead
- **Better User Experience:** Faster page load, all data at once

### Implementation Considerations
- **Optional Chart Loading:** Use `include_charts=false` to get only KPIs when needed
- **Lazy Loading:** Frontend can request charts on-demand if needed
- **Progressive Enhancement:** Load KPIs first, then charts
- **Error Handling:** If one chart fails, others still return
- **Timeout Management:** Set appropriate timeouts for dashboard queries

### Best Practices
- All dashboard endpoints should support filtering by date range
- All aggregations should exclude soft-deleted records (`is_deleted = false`)
- All timestamps should be in IST timezone
- Dashboard data should be read-only (no mutations)
- Consider rate limiting for dashboard endpoints to prevent abuse
- Add proper error handling for missing data scenarios
- Use database transactions for consistency in parallel queries
- Monitor query performance and optimize slow queries
- Add logging for dashboard access and performance metrics