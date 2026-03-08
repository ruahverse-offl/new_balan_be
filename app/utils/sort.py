"""
Sort Utilities
Helper functions for building sort queries
"""

from typing import Optional, List
from sqlalchemy.orm import DeclarativeMeta
from sqlalchemy import asc, desc


def build_sort_order(model_class: DeclarativeMeta, sort_by: Optional[str], sort_order: Optional[str]):
    """
    Build SQLAlchemy order_by clause.
    
    Args:
        model_class: SQLAlchemy model class
        sort_by: Field name to sort by (comma-separated for multiple fields)
        sort_order: Sort order 'asc' or 'desc' (comma-separated for multiple fields)
        
    Returns:
        List of order_by clauses or None
        
    Raises:
        ValueError: If field doesn't exist in model
    """
    if not sort_by:
        return None
    
    # Default to descending order
    if not sort_order:
        sort_order = "desc"
    
    # Handle multiple sort fields
    sort_fields = [f.strip() for f in sort_by.split(",")]
    sort_orders = [o.strip().lower() for o in sort_order.split(",")]
    
    # Extend sort_orders if fewer than sort_fields
    while len(sort_orders) < len(sort_fields):
        sort_orders.append("desc")
    
    order_clauses = []
    
    for field_name, order in zip(sort_fields, sort_orders):
        if not hasattr(model_class, field_name):
            raise ValueError(f"Field '{field_name}' does not exist in {model_class.__name__}")
        
        column = getattr(model_class, field_name)
        
        if order == "asc":
            order_clauses.append(asc(column))
        else:
            order_clauses.append(desc(column))
    
    return order_clauses if order_clauses else None


def apply_sort(query, model_class: DeclarativeMeta, sort_by: Optional[str], sort_order: Optional[str]):
    """
    Apply sort to a query.
    
    Args:
        query: SQLAlchemy query object
        model_class: SQLAlchemy model class
        sort_by: Field name to sort by
        sort_order: Sort order 'asc' or 'desc'
        
    Returns:
        Query with sort applied
    """
    order_clauses = build_sort_order(model_class, sort_by, sort_order)
    if order_clauses:
        return query.order_by(*order_clauses)
    
    # Default sort by created_at descending
    if hasattr(model_class, "created_at"):
        return query.order_by(desc(model_class.created_at))
    
    return query
