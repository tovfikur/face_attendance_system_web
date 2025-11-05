"""
User and authentication schemas.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ============================================================================
# Authentication Schemas
# ============================================================================


class LoginRequest(BaseModel):
    """User login request."""

    username: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password", min_length=1)


class TokenResponse(BaseModel):
    """Token response."""

    accessToken: str = Field(..., description="JWT access token")
    refreshToken: str = Field(..., description="JWT refresh token")
    tokenType: str = Field(default="bearer", description="Token type")
    expiresIn: int = Field(..., description="Token expiration in seconds")


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""

    refreshToken: str = Field(..., description="Refresh token")


class LoginResponse(BaseModel):
    """Login response."""

    accessToken: str = Field(..., description="JWT access token")
    refreshToken: str = Field(..., description="JWT refresh token")
    user: "UserResponse" = Field(..., description="User information")


class LogoutRequest(BaseModel):
    """Logout request."""

    refreshToken: str = Field(..., description="Refresh token to revoke")


# ============================================================================
# User Schemas
# ============================================================================


class UserBase(BaseModel):
    """User base schema."""

    name: str = Field(..., description="User name", min_length=1, max_length=255)
    email: EmailStr = Field(..., description="User email")
    roleId: str = Field(..., description="Role ID")


class UserCreate(UserBase):
    """User creation schema."""

    password: Optional[str] = Field(None, description="Initial password (if not set, send reset email)")


class UserUpdate(BaseModel):
    """User update schema."""

    name: Optional[str] = Field(None, description="User name", min_length=1, max_length=255)
    email: Optional[EmailStr] = Field(None, description="User email")
    roleId: Optional[str] = Field(None, description="Role ID")
    status: Optional[str] = Field(None, description="User status: active, suspended")


class UserResponse(BaseModel):
    """User response schema."""

    id: str = Field(..., description="User ID")
    name: str = Field(..., description="User name")
    email: str = Field(..., description="User email")
    roleId: str = Field(..., description="Role ID")
    status: str = Field(..., description="User status")
    lastActive: Optional[datetime] = Field(None, description="Last active timestamp")
    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: datetime = Field(..., description="Update timestamp")

    class Config:
        """Schema config."""

        from_attributes = True


class UserListResponse(BaseModel):
    """User list response."""

    users: list[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total users")


class ChangePasswordRequest(BaseModel):
    """Change password request."""

    currentPassword: str = Field(..., description="Current password")
    newPassword: str = Field(..., description="New password", min_length=8)
    confirmPassword: str = Field(..., description="Password confirmation")


class PasswordResetRequest(BaseModel):
    """Password reset request."""

    email: EmailStr = Field(..., description="User email")


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation."""

    token: str = Field(..., description="Reset token")
    password: str = Field(..., description="New password", min_length=8)


# ============================================================================
# Role Schemas
# ============================================================================


class RoleResponse(BaseModel):
    """Role response schema."""

    id: str = Field(..., description="Role ID")
    name: str = Field(..., description="Role name")
    permissions: list[str] = Field(..., description="Role permissions")
    description: Optional[str] = Field(None, description="Role description")
    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: datetime = Field(..., description="Update timestamp")

    class Config:
        """Schema config."""

        from_attributes = True


class CurrentUserResponse(BaseModel):
    """Current user response."""

    user: UserResponse = Field(..., description="User information")
    permissions: list[str] = Field(..., description="User permissions")


__all__ = [
    "LoginRequest",
    "TokenResponse",
    "RefreshTokenRequest",
    "LoginResponse",
    "LogoutRequest",
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserListResponse",
    "ChangePasswordRequest",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    "RoleResponse",
    "CurrentUserResponse",
]
