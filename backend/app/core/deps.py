"""
FastAPI dependencies for authentication and database access.
"""

import json
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import AuthenticationError
from app.core.security import verify_token
from app.db.session import get_db

security = HTTPBearer()


class CurrentUser:
    """Current user information from JWT token."""

    def __init__(self, user_id: str, email: str, role_id: str, permissions: list[str]):
        """Initialize current user."""
        self.user_id = user_id
        self.email = email
        self.role_id = role_id
        self.permissions = permissions

    def has_permission(self, permission: str) -> bool:
        """Check if user has permission."""
        return "*" in self.permissions or permission in self.permissions

    def __repr__(self) -> str:
        return f"<CurrentUser user_id={self.user_id} email={self.email}>"


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:
    """Get current user from JWT token."""
    try:
        token = credentials.credentials
        payload = verify_token(token)

        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        role_id: str = payload.get("role_id")
        permissions_str: str = payload.get("permissions", "[]")

        if not user_id:
            raise AuthenticationError("Invalid token")

        # Parse permissions (stored as JSON string in token)
        try:
            permissions = json.loads(permissions_str) if isinstance(permissions_str, str) else permissions_str
        except (json.JSONDecodeError, TypeError):
            permissions = []

        return CurrentUser(user_id=user_id, email=email, role_id=role_id, permissions=permissions)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[CurrentUser]:
    """Get optional current user (may be None)."""
    if not credentials:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def require_permission(permission: str):
    """Dependency to require a specific permission."""

    async def permission_checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        """Check if user has permission."""
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return permission_checker


def require_role(role_id: str):
    """Dependency to require a specific role."""

    async def role_checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        """Check if user has role."""
        if current_user.role_id != role_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_checker


__all__ = [
    "get_current_user",
    "get_optional_user",
    "require_permission",
    "require_role",
    "CurrentUser",
]
