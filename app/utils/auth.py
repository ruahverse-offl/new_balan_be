"""
Authentication Utilities
JWT and user authentication helpers
"""

from typing import Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.jwt_token import decode_token

security = HTTPBearer()


def get_user_id_from_token(token: str) -> UUID:
    """Decode a JWT token and return the user UUID from the 'sub' claim."""
    payload = decode_token(token)
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing subject",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return UUID(user_id_str)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UUID:
    """
    Get current user ID from JWT token.

    Args:
        credentials: HTTP Bearer token credentials

    Returns:
        Current user ID as UUID

    Raises:
        HTTPException: If token is invalid or missing
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    token = credentials.credentials

    # Check if token is blacklisted (logout)
    from app.routes.auth_router import is_token_blacklisted
    if is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Decode token and get user ID
    try:
        user_id = get_user_id_from_token(token)
        return user_id
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_user_id_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    )
) -> Optional[UUID]:
    """
    Get current user ID (optional).
    Returns None if no valid token is provided.
    """
    if not credentials:
        return None
    try:
        return get_user_id_from_token(credentials.credentials)
    except Exception:
        return None
