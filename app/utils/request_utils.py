"""
Request Utilities
Helper functions for extracting request information
"""

from fastapi import Request
from typing import Optional


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request headers.
    
    Checks in order:
    1. X-Forwarded-For (for proxies/load balancers)
    2. X-Real-IP (for nginx)
    3. Direct client IP
    
    Args:
        request: FastAPI Request object
        
    Returns:
        IP address string (supports IPv4 and IPv6, max 45 chars)
    """
    # Check X-Forwarded-For header (first IP in chain)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first one
        ip = forwarded_for.split(",")[0].strip()
        if ip:
            return ip
    
    # Check X-Real-IP header (nginx)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # Fallback to direct client IP
    if request.client:
        return request.client.host
    
    # Default fallback
    return "0.0.0.0"
