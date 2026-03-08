"""
Inventory Dashboard Repository
Database queries for inventory dashboard aggregations
"""

from typing import Dict, List, Optional
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case, cast, Date, text
from sqlalchemy.orm import aliased

from app.db.models import (
    ProductBatch,
    MedicineBrand,
    Medicine,
    TherapeuticCategory,
    InventoryTransaction,
    OrderItem,
    Order
)


class InventoryDashboardRepository:
    """Repository for inventory dashboard data aggregation."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_kpis(self, low_stock_threshold: int = 10, expiry_days: int = 30) -> Dict:
        """Get inventory KPIs."""
        today = date.today()
        expiry_date_threshold = today + timedelta(days=expiry_days)
        
        # Total stock value and quantity
        stock_value_query = select(
            func.coalesce(func.sum(ProductBatch.quantity_available * ProductBatch.purchase_price), 0).label("total_stock_value"),
            func.coalesce(func.sum(ProductBatch.quantity_available), 0).label("total_stock_quantity"),
            func.count(func.distinct(ProductBatch.medicine_brand_id)).label("total_active_products"),
            func.count(ProductBatch.id).label("total_batches")
        ).where(
            and_(
                ProductBatch.quantity_available > 0,
                ProductBatch.is_deleted == False
            )
        )
        
        stock_value_result = await self.session.execute(stock_value_query)
        stock_value_row = stock_value_result.first()
        
        # Low stock count
        low_stock_query = select(func.count(func.distinct(ProductBatch.medicine_brand_id))).select_from(
            ProductBatch
        ).join(
            MedicineBrand, ProductBatch.medicine_brand_id == MedicineBrand.id
        ).where(
            and_(
                ProductBatch.quantity_available > 0,
                ProductBatch.quantity_available <= low_stock_threshold,
                ProductBatch.is_deleted == False,
                MedicineBrand.is_deleted == False
            )
        )
        
        low_stock_result = await self.session.execute(low_stock_query)
        low_stock_count = low_stock_result.scalar() or 0
        
        # Out of stock count
        out_of_stock_query = select(func.count(func.distinct(MedicineBrand.id))).select_from(
            MedicineBrand
        ).outerjoin(
            ProductBatch, and_(
                ProductBatch.medicine_brand_id == MedicineBrand.id,
                ProductBatch.quantity_available > 0,
                ProductBatch.is_deleted == False
            )
        ).where(
            and_(
                MedicineBrand.is_deleted == False,
                MedicineBrand.is_active == True,
                ProductBatch.id == None  # No active batches
            )
        )
        
        out_of_stock_result = await self.session.execute(out_of_stock_query)
        out_of_stock_count = out_of_stock_result.scalar() or 0
        
        # Expiring soon count
        expiring_soon_query = select(func.count(ProductBatch.id)).where(
            and_(
                ProductBatch.expiry_date <= expiry_date_threshold,
                ProductBatch.expiry_date > today,
                ProductBatch.quantity_available > 0,
                ProductBatch.is_deleted == False
            )
        )
        
        expiring_soon_result = await self.session.execute(expiring_soon_query)
        expiring_soon_count = expiring_soon_result.scalar() or 0
        
        # Expired count
        expired_query = select(func.count(ProductBatch.id)).where(
            and_(
                ProductBatch.expiry_date < today,
                ProductBatch.quantity_available > 0,
                ProductBatch.is_deleted == False
            )
        )
        
        expired_result = await self.session.execute(expired_query)
        expired_count = expired_result.scalar() or 0
        
        # Calculate averages
        total_stock_value = Decimal(str(stock_value_row.total_stock_value or 0))
        total_active_products = stock_value_row.total_active_products or 0
        average_stock_value = total_stock_value / total_active_products if total_active_products > 0 else None

        # Calculate stock turnover rate = COGS / Average Inventory Value (last 365 days)
        cogs_period_start = today - timedelta(days=365)
        cogs_query = select(
            func.coalesce(
                func.sum(OrderItem.quantity * OrderItem.unit_price), 0
            ).label("cogs")
        ).select_from(OrderItem).join(
            Order, OrderItem.order_id == Order.id
        ).where(
            and_(
                Order.order_status.in_(["DELIVERED", "COMPLETED"]),
                Order.is_deleted == False,
                OrderItem.is_deleted == False,
                func.date(Order.created_at) >= cogs_period_start
            )
        )
        cogs_result = await self.session.execute(cogs_query)
        cogs = Decimal(str(cogs_result.scalar() or 0))

        stock_turnover_rate = None
        if total_stock_value and total_stock_value > 0:
            stock_turnover_rate = round(float(cogs / total_stock_value), 2)

        return {
            "total_stock_value": total_stock_value,
            "total_stock_quantity": stock_value_row.total_stock_quantity or 0,
            "total_active_products": total_active_products,
            "total_batches": stock_value_row.total_batches or 0,
            "low_stock_count": low_stock_count,
            "out_of_stock_count": out_of_stock_count,
            "expiring_soon_count": expiring_soon_count,
            "expired_count": expired_count,
            "stock_turnover_rate": stock_turnover_rate,
            "average_stock_value": average_stock_value
        }
    
    async def get_alerts(
        self,
        low_stock_threshold: int = 10,
        expiry_days: int = 30
    ) -> List[Dict]:
        """Get inventory alerts."""
        alerts = []
        today = date.today()
        expiry_date_threshold = today + timedelta(days=expiry_days)
        
        # Low stock alerts
        low_stock_query = select(
            ProductBatch.medicine_brand_id,
            MedicineBrand.brand_name,
            func.sum(ProductBatch.quantity_available).label("current_quantity")
        ).select_from(
            ProductBatch
        ).join(
            MedicineBrand, ProductBatch.medicine_brand_id == MedicineBrand.id
        ).where(
            and_(
                ProductBatch.quantity_available > 0,
                ProductBatch.quantity_available <= low_stock_threshold,
                ProductBatch.is_deleted == False,
                MedicineBrand.is_deleted == False
            )
        ).group_by(
            ProductBatch.medicine_brand_id,
            MedicineBrand.brand_name
        )
        
        low_stock_result = await self.session.execute(low_stock_query)
        for row in low_stock_result:
            alerts.append({
                "type": "LOW_STOCK",
                "severity": "WARNING",
                "message": f"{row.brand_name} is running low ({row.current_quantity} units remaining)",
                "medicine_brand_id": row.medicine_brand_id,
                "medicine_brand_name": row.brand_name,
                "current_quantity": int(row.current_quantity),
                "threshold": low_stock_threshold
            })
        
        # Out of stock alerts
        out_of_stock_query = select(
            MedicineBrand.id,
            MedicineBrand.brand_name
        ).select_from(
            MedicineBrand
        ).outerjoin(
            ProductBatch, and_(
                ProductBatch.medicine_brand_id == MedicineBrand.id,
                ProductBatch.quantity_available > 0,
                ProductBatch.is_deleted == False
            )
        ).where(
            and_(
                MedicineBrand.is_deleted == False,
                MedicineBrand.is_active == True,
                ProductBatch.id == None
            )
        ).limit(20)  # Limit to prevent too many alerts
        
        out_of_stock_result = await self.session.execute(out_of_stock_query)
        for row in out_of_stock_result:
            alerts.append({
                "type": "OUT_OF_STOCK",
                "severity": "CRITICAL",
                "message": f"{row.brand_name} is out of stock",
                "medicine_brand_id": row.id,
                "medicine_brand_name": row.brand_name,
                "current_quantity": 0
            })
        
        # Expiring soon alerts
        expiring_soon_query = select(
            ProductBatch.id,
            ProductBatch.batch_number,
            ProductBatch.expiry_date,
            ProductBatch.quantity_available,
            MedicineBrand.brand_name
        ).select_from(
            ProductBatch
        ).join(
            MedicineBrand, ProductBatch.medicine_brand_id == MedicineBrand.id
        ).where(
            and_(
                ProductBatch.expiry_date <= expiry_date_threshold,
                ProductBatch.expiry_date > today,
                ProductBatch.quantity_available > 0,
                ProductBatch.is_deleted == False,
                MedicineBrand.is_deleted == False
            )
        ).order_by(
            ProductBatch.expiry_date
        ).limit(20)
        
        expiring_soon_result = await self.session.execute(expiring_soon_query)
        for row in expiring_soon_result:
            days_until_expiry = (row.expiry_date - today).days
            alerts.append({
                "type": "EXPIRING_SOON",
                "severity": "WARNING",
                "message": f"Batch {row.batch_number} expires in {days_until_expiry} days",
                "batch_id": row.id,
                "batch_number": row.batch_number,
                "medicine_brand_name": row.brand_name,
                "expiry_date": str(row.expiry_date),
                "quantity_available": row.quantity_available
            })
        
        # Expired alerts
        expired_query = select(
            ProductBatch.id,
            ProductBatch.batch_number,
            ProductBatch.expiry_date,
            ProductBatch.quantity_available,
            MedicineBrand.brand_name
        ).select_from(
            ProductBatch
        ).join(
            MedicineBrand, ProductBatch.medicine_brand_id == MedicineBrand.id
        ).where(
            and_(
                ProductBatch.expiry_date < today,
                ProductBatch.quantity_available > 0,
                ProductBatch.is_deleted == False,
                MedicineBrand.is_deleted == False
            )
        ).limit(20)
        
        expired_result = await self.session.execute(expired_query)
        for row in expired_result:
            alerts.append({
                "type": "EXPIRED",
                "severity": "CRITICAL",
                "message": f"Batch {row.batch_number} has expired",
                "batch_id": row.id,
                "batch_number": row.batch_number,
                "medicine_brand_name": row.brand_name,
                "expiry_date": str(row.expiry_date),
                "quantity_available": row.quantity_available
            })
        
        return alerts
    
    async def get_stock_value_trend(self, days: int = 30) -> List[Dict]:
        """Get stock value trend over time."""
        # For now, return current value (can be enhanced with historical data)
        kpis = await self.get_kpis()
        return [{
            "date": str(date.today()),
            "value": kpis["total_stock_value"]
        }]
    
    async def get_stock_by_category(self) -> List[Dict]:
        """Get stock levels by therapeutic category."""
        query = select(
            TherapeuticCategory.name.label("category"),
            func.sum(ProductBatch.quantity_available).label("quantity"),
            func.sum(ProductBatch.quantity_available * ProductBatch.purchase_price).label("value")
        ).select_from(
            ProductBatch
        ).join(
            MedicineBrand, ProductBatch.medicine_brand_id == MedicineBrand.id
        ).join(
            Medicine, MedicineBrand.medicine_id == Medicine.id
        ).join(
            TherapeuticCategory, Medicine.therapeutic_category_id == TherapeuticCategory.id
        ).where(
            and_(
                ProductBatch.quantity_available > 0,
                ProductBatch.is_deleted == False,
                MedicineBrand.is_deleted == False,
                Medicine.is_deleted == False,
                TherapeuticCategory.is_deleted == False
            )
        ).group_by(
            TherapeuticCategory.name
        ).order_by(
            func.sum(ProductBatch.quantity_available * ProductBatch.purchase_price).desc()
        )
        
        result = await self.session.execute(query)
        return [
            {
                "label": row.category,
                "quantity": int(row.quantity),
                "value": Decimal(str(row.value))
            }
            for row in result
        ]
    
    async def get_top_products(self, limit: int = 10) -> List[Dict]:
        """Get top products by stock value."""
        query = select(
            MedicineBrand.brand_name,
            func.sum(ProductBatch.quantity_available * ProductBatch.purchase_price).label("value")
        ).select_from(
            ProductBatch
        ).join(
            MedicineBrand, ProductBatch.medicine_brand_id == MedicineBrand.id
        ).where(
            and_(
                ProductBatch.quantity_available > 0,
                ProductBatch.is_deleted == False,
                MedicineBrand.is_deleted == False
            )
        ).group_by(
            MedicineBrand.brand_name
        ).order_by(
            func.sum(ProductBatch.quantity_available * ProductBatch.purchase_price).desc()
        ).limit(limit)
        
        result = await self.session.execute(query)
        return [
            {
                "label": row.brand_name,
                "value": Decimal(str(row.value))
            }
            for row in result
        ]
    
    async def get_stock_distribution(self, low_stock_threshold: int = 10) -> List[Dict]:
        """Get stock distribution (low/normal/out)."""
        kpis = await self.get_kpis(low_stock_threshold)
        
        # Calculate normal stock (active products - low stock - out of stock)
        normal_stock = max(0, kpis["total_active_products"] - kpis["low_stock_count"] - kpis["out_of_stock_count"])
        
        return [
            {"label": "Low Stock", "count": kpis["low_stock_count"]},
            {"label": "Normal Stock", "count": normal_stock},
            {"label": "Out of Stock", "count": kpis["out_of_stock_count"]}
        ]
    
    async def get_expiry_timeline(self, months: int = 6) -> List[Dict]:
        """Get expiry timeline for next N months."""
        today = date.today()
        end_date = today + timedelta(days=months * 30)
        
        # Create the date_trunc expression once and reuse it
        month_trunc = func.date_trunc('month', ProductBatch.expiry_date)
        
        query = select(
            month_trunc.label("month"),
            func.count(ProductBatch.id).label("batch_count")
        ).where(
            and_(
                ProductBatch.expiry_date >= today,
                ProductBatch.expiry_date <= end_date,
                ProductBatch.quantity_available > 0,
                ProductBatch.is_deleted == False
            )
        ).group_by(
            month_trunc
        ).order_by(
            month_trunc
        )
        
        result = await self.session.execute(query)
        return [
            {
                "label": str(row.month)[:7],  # YYYY-MM format
                "count": row.batch_count
            }
            for row in result
        ]
    
    async def get_stock_movement(self, days: int = 30) -> List[Dict]:
        """Get stock movement trend."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        query = select(
            func.date(InventoryTransaction.created_at).label("date"),
            func.sum(InventoryTransaction.quantity_change).label("quantity_change")
        ).where(
            and_(
                func.date(InventoryTransaction.created_at) >= start_date,
                func.date(InventoryTransaction.created_at) <= end_date,
                InventoryTransaction.is_deleted == False
            )
        ).group_by(
            func.date(InventoryTransaction.created_at)
        ).order_by(
            func.date(InventoryTransaction.created_at)
        )
        
        result = await self.session.execute(query)
        return [
            {
                "date": str(row.date),
                "quantity": int(row.quantity_change or 0)
            }
            for row in result
        ]
    
    async def get_stock_by_dosage_form(self) -> List[Dict]:
        """Get stock by dosage form."""
        query = select(
            Medicine.dosage_form,
            func.count(func.distinct(MedicineBrand.id)).label("count")
        ).select_from(
            ProductBatch
        ).join(
            MedicineBrand, ProductBatch.medicine_brand_id == MedicineBrand.id
        ).join(
            Medicine, MedicineBrand.medicine_id == Medicine.id
        ).where(
            and_(
                ProductBatch.quantity_available > 0,
                ProductBatch.is_deleted == False,
                MedicineBrand.is_deleted == False,
                Medicine.is_deleted == False
            )
        ).group_by(
            Medicine.dosage_form
        )
        
        result = await self.session.execute(query)
        return [
            {
                "label": row.dosage_form,
                "count": row.count
            }
            for row in result
        ]
