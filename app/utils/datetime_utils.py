"""
DateTime Utilities
Helper functions for timezone handling (IST)
"""

from datetime import datetime, timezone, timedelta

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))


def get_current_ist_time() -> datetime:
    """
    Get current time in IST timezone.
    
    Returns:
        Current datetime in IST timezone
    """
    return datetime.now(IST)


def convert_to_ist(dt: datetime) -> datetime:
    """
    Convert datetime to IST timezone.
    
    If datetime is naive, assumes it's already in IST.
    If datetime has timezone info, converts to IST.
    
    Args:
        dt: Datetime to convert
        
    Returns:
        Datetime in IST timezone
    """
    if dt.tzinfo is None:
        # Naive datetime - assume it's IST
        return dt.replace(tzinfo=IST)
    else:
        # Convert to IST
        return dt.astimezone(IST)


def format_datetime_ist(dt: datetime) -> str:
    """
    Format datetime to ISO string in IST.
    
    Args:
        dt: Datetime to format
        
    Returns:
        ISO formatted string with IST timezone
    """
    ist_dt = convert_to_ist(dt) if dt.tzinfo else dt.replace(tzinfo=IST)
    return ist_dt.isoformat()
