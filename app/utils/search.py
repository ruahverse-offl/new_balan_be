"""
Search Utilities
Helper functions for building search queries
"""

from typing import List, Any
from sqlalchemy import Column, String, Text, or_, and_
from sqlalchemy.orm import DeclarativeMeta


def build_search_filter(model_class: DeclarativeMeta, search_term: str, searchable_fields: List[str]) -> List[Any]:
    """
    Build SQLAlchemy filter conditions for search across multiple fields.
    
    Args:
        model_class: SQLAlchemy model class
        search_term: Search term to match
        searchable_fields: List of field names to search in
        
    Returns:
        List of filter conditions (OR conditions for ILIKE matching)
    """
    if not search_term or not searchable_fields:
        return []
    
    conditions = []
    search_pattern = f"%{search_term}%"
    
    for field_name in searchable_fields:
        if hasattr(model_class, field_name):
            column = getattr(model_class, field_name)
            # Only search in String and Text columns
            if isinstance(column.type, (String, Text)):
                conditions.append(column.ilike(search_pattern))
    
    return conditions if conditions else []


def apply_search_filter(query, model_class: DeclarativeMeta, search_term: str, searchable_fields: List[str]):
    """
    Apply search filter to a query.
    
    Args:
        query: SQLAlchemy query object
        model_class: SQLAlchemy model class
        search_term: Search term to match
        searchable_fields: List of field names to search in
        
    Returns:
        Query with search filters applied
    """
    if not search_term:
        return query
    
    search_conditions = build_search_filter(model_class, search_term, searchable_fields)
    if search_conditions:
        return query.filter(or_(*search_conditions))
    
    return query
