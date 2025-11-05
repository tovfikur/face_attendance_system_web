"""
Common schemas for API responses and requests.
"""

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Error detail."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[dict[str, Any]] = Field(None, description="Additional details")


class SuccessResponse(BaseModel, Generic[T]):
    """Success response envelope."""

    success: bool = Field(True)
    data: T = Field(..., description="Response data")
    meta: Optional[dict[str, Any]] = Field(None, description="Response metadata")


class ErrorResponse(BaseModel):
    """Error response envelope."""

    success: bool = Field(False)
    error: ErrorDetail = Field(..., description="Error details")
    requestId: str = Field(..., description="Request ID for tracking")


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    page: int = Field(..., description="Current page number")
    pageSize: int = Field(..., description="Items per page")
    total: int = Field(..., description="Total items")
    totalPages: int = Field(..., description="Total pages")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response."""

    success: bool = Field(True)
    data: list[T] = Field(..., description="Response data")
    meta: PaginationMeta = Field(..., description="Pagination metadata")


class HealthStatus(BaseModel):
    """Health status."""

    status: str = Field(..., description="Health status: alive, dead")
    timestamp: str = Field(..., description="Check timestamp")
    version: str = Field(..., description="Application version")


__all__ = [
    "ErrorDetail",
    "SuccessResponse",
    "ErrorResponse",
    "PaginationMeta",
    "PaginatedResponse",
    "HealthStatus",
]
