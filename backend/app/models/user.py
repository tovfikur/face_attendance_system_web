"""
User, Role, and authentication models.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, String, Text, UUID, Boolean, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Role(Base):
    """Role model for RBAC."""

    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    permissions: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON array
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<Role id={self.id} name={self.name}>"


class User(Base, TimestampMixin):
    """User model."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    last_active: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(default=1)

    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_role_id", "role_id"),
        Index("idx_users_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} name={self.name}>"


class UserSession(Base):
    """User session/refresh token model."""

    __tablename__ = "user_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    refresh_token: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())

    __table_args__ = (
        Index("idx_user_sessions_user_id", "user_id"),
        Index("idx_user_sessions_expires", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<UserSession user_id={self.user_id}>"


class UserPreferences(Base, TimestampMixin):
    """User preferences model."""

    __tablename__ = "user_preferences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    theme: Mapped[str] = mapped_column(String(20), nullable=False, default="dark")
    grid_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="3x3")
    auto_rotate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="UTC")
    preferences: Mapped[str] = mapped_column(Text, nullable=False, default="{}")  # JSON

    def __repr__(self) -> str:
        return f"<UserPreferences user_id={self.user_id}>"
