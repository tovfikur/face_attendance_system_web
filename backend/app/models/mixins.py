"""
Database model mixins for common functionality.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, String, func
from sqlalchemy.orm import declarative_mixin


@declarative_mixin
class TimestampMixin:
    """Mixin for adding created_at and updated_at timestamps to models."""

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        doc="When the record was created"
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        doc="When the record was last updated"
    )


@declarative_mixin
class CreatedByMixin:
    """Mixin for tracking who created a record."""

    created_by = Column(
        String(255),
        nullable=True,
        doc="User who created the record"
    )


@declarative_mixin
class SoftDeleteMixin:
    """Mixin for soft delete functionality."""

    deleted_at = Column(
        DateTime,
        nullable=True,
        default=None,
        doc="When the record was soft deleted"
    )

    def soft_delete(self):
        """Mark record as deleted without actually deleting it."""
        self.deleted_at = datetime.utcnow()
