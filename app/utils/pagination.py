"""
Pagination Utilities
Helper functions for pagination calculations
"""

from typing import Dict


def calculate_pagination(total: int, limit: int, offset: int) -> Dict[str, any]:
    """
    Calculate pagination metadata.
    
    Args:
        total: Total number of records
        limit: Number of records per page
        offset: Number of records skipped
        
    Returns:
        Dictionary with pagination metadata
    """
    has_next = (offset + limit) < total
    has_previous = offset > 0
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_next": has_next,
        "has_previous": has_previous
    }
