"""
Sales Dashboard Repository
Database queries for sales dashboard aggregations
"""

from typing import Dict, List
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.db.models import InventoryTransaction, Order, MedicineBrand, Medicine, TherapeuticCategory


class SalesDashboardRepository:
    """Repository for sales dashboard data aggregation."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_kpis(self, days: int = 30) -> Dict:
        """Get sales KPIs."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Total sales quantity (from inventory transactions with type SALE)
        sales_quantity_query = select(
            func.coalesce(func.sum(func.abs(InventoryTransaction.quantity_change)), 0).label("total_sales")
        ).where(
            and_(
                InventoryTransaction.transaction_type == "SALE",
                func.date(InventoryTransaction.created_at) >= start_date,
                func.date(InventoryTransaction.created_at) <= end_date,
                InventoryTransaction.is_deleted == False
            )
        )
        
        sales_quantity_result = await self.session.execute(sales_quantity_query)
        total_sales_quantity = sales_quantity_result.scalar() or 0
        
        # Top selling product
        top_product_query = select(
            MedicineBrand.brand_name,
            func.sum(func.abs(InventoryTransaction.quantity_change)).label("quantity")
        ).select_from(
            InventoryTransaction
        ).join(
            MedicineBrand, InventoryTransaction.medicine_brand_id == MedicineBrand.id
        ).where(
            and_(
                InventoryTransaction.transaction_type == "SALE",
                func.date(InventoryTransaction.created_at) >= start_date,
                func.date(InventoryTransaction.created_at) <= end_date,
                InventoryTransaction.is_deleted == False,
                MedicineBrand.is_deleted == False
            )
        ).group_by(
            MedicineBrand.brand_name
        ).order_by(
            func.sum(func.abs(InventoryTransaction.quantity_change)).desc()
        ).limit(1)
        
        top_product_result = await self.session.execute(top_product_query)
        top_product_row = top_product_result.first()
        top_selling_product = top_product_row.brand_name if top_product_row else None
        
        # Average sales per day
        avg_sales_per_day = total_sales_quantity / days if days > 0 else None
        
        # Customer count (unique customers who placed orders)
        customer_count_query = select(
            func.count(func.distinct(Order.customer_id)).label("customer_count")
        ).where(
            and_(
                func.date(Order.created_at) >= start_date,
                func.date(Order.created_at) <= end_date,
                Order.is_deleted == False
            )
        )
        
        customer_count_result = await self.session.execute(customer_count_query)
        customer_count = customer_count_result.scalar() or 0
        
        # Sales growth rate (compare with previous period)
        prev_start_date = start_date - timedelta(days=days)
        prev_sales_query = select(
            func.coalesce(func.sum(func.abs(InventoryTransaction.quantity_change)), 0).label("prev_sales")
        ).where(
            and_(
                InventoryTransaction.transaction_type == "SALE",
                func.date(InventoryTransaction.created_at) >= prev_start_date,
                func.date(InventoryTransaction.created_at) < start_date,
                InventoryTransaction.is_deleted == False
            )
        )
        
        prev_sales_result = await self.session.execute(prev_sales_query)
        prev_sales = prev_sales_result.scalar() or 0
        
        sales_growth_rate = None
        if prev_sales > 0:
            sales_growth_rate = ((total_sales_quantity - prev_sales) / prev_sales) * 100
        
        return {
            "total_sales_quantity": total_sales_quantity,
            "top_selling_product": top_selling_product,
            "sales_growth_rate": Decimal(str(sales_growth_rate)) if sales_growth_rate else None,
            "average_sales_per_day": Decimal(str(avg_sales_per_day)) if avg_sales_per_day else None,
            "customer_count": customer_count
        }
    
    async def get_top_products(self, limit: int = 10, days: int = 30) -> List[Dict]:
        """Get top selling products."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        query = select(
            MedicineBrand.brand_name,
            func.sum(func.abs(InventoryTransaction.quantity_change)).label("quantity")
        ).select_from(
            InventoryTransaction
        ).join(
            MedicineBrand, InventoryTransaction.medicine_brand_id == MedicineBrand.id
        ).where(
            and_(
                InventoryTransaction.transaction_type == "SALE",
                func.date(InventoryTransaction.created_at) >= start_date,
                func.date(InventoryTransaction.created_at) <= end_date,
                InventoryTransaction.is_deleted == False,
                MedicineBrand.is_deleted == False
            )
        ).group_by(
            MedicineBrand.brand_name
        ).order_by(
            func.sum(func.abs(InventoryTransaction.quantity_change)).desc()
        ).limit(limit)
        
        result = await self.session.execute(query)
        return [
            {
                "label": row.brand_name,
                "quantity": int(row.quantity)
            }
            for row in result
        ]
    
    async def get_sales_by_category(self, days: int = 30) -> List[Dict]:
        """Get sales by therapeutic category."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        query = select(
            TherapeuticCategory.name.label("category"),
            func.sum(func.abs(InventoryTransaction.quantity_change)).label("quantity")
        ).select_from(
            InventoryTransaction
        ).join(
            MedicineBrand, InventoryTransaction.medicine_brand_id == MedicineBrand.id
        ).join(
            Medicine, MedicineBrand.medicine_id == Medicine.id
        ).join(
            TherapeuticCategory, Medicine.therapeutic_category_id == TherapeuticCategory.id
        ).where(
            and_(
                InventoryTransaction.transaction_type == "SALE",
                func.date(InventoryTransaction.created_at) >= start_date,
                func.date(InventoryTransaction.created_at) <= end_date,
                InventoryTransaction.is_deleted == False,
                MedicineBrand.is_deleted == False,
                Medicine.is_deleted == False,
                TherapeuticCategory.is_deleted == False
            )
        ).group_by(
            TherapeuticCategory.name
        ).order_by(
            func.sum(func.abs(InventoryTransaction.quantity_change)).desc()
        )
        
        result = await self.session.execute(query)
        return [
            {
                "label": row.category,
                "quantity": int(row.quantity)
            }
            for row in result
        ]
    
    async def get_sales_trend(self, days: int = 30) -> List[Dict]:
        """Get sales trend over time."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        query = select(
            func.date(InventoryTransaction.created_at).label("date"),
            func.sum(func.abs(InventoryTransaction.quantity_change)).label("quantity")
        ).where(
            and_(
                InventoryTransaction.transaction_type == "SALE",
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
                "quantity": int(row.quantity)
            }
            for row in result
        ]
    
    async def get_sales_by_dosage_form(self, days: int = 30) -> List[Dict]:
        """Get sales by dosage form."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        query = select(
            Medicine.dosage_form,
            func.sum(func.abs(InventoryTransaction.quantity_change)).label("quantity")
        ).select_from(
            InventoryTransaction
        ).join(
            MedicineBrand, InventoryTransaction.medicine_brand_id == MedicineBrand.id
        ).join(
            Medicine, MedicineBrand.medicine_id == Medicine.id
        ).where(
            and_(
                InventoryTransaction.transaction_type == "SALE",
                func.date(InventoryTransaction.created_at) >= start_date,
                func.date(InventoryTransaction.created_at) <= end_date,
                InventoryTransaction.is_deleted == False,
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
                "quantity": int(row.quantity)
            }
            for row in result
        ]
