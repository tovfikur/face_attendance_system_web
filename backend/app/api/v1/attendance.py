"""Attendance management endpoints."""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_current_user
from app.core.errors import NotFoundError
from app.db.session import get_db
from app.schemas.common import PaginatedResponse, PaginationMeta, SuccessResponse
from app.schemas.person import (
    AttendanceResponse,
    AttendanceStatistics,
    CheckInRequest,
    CheckInResponse,
    CheckOutRequest,
    CheckOutResponse,
    PersonCurrentStatus,
)
from app.services.attendance_service import AttendanceService

router = APIRouter(tags=["Attendance"])
logger = logging.getLogger(__name__)


# Helper functions
async def get_attendance_service(db: AsyncSession = Depends(get_db)) -> AttendanceService:
    """Get attendance service."""
    return AttendanceService(db)


# ============================================================================
# Check-in/Check-out Endpoints
# ============================================================================


@router.post("/check-in", response_model=SuccessResponse[CheckInResponse])
async def check_in(
    request: CheckInRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: AttendanceService = Depends(get_attendance_service),
) -> SuccessResponse[CheckInResponse]:
    """Record check-in for a person."""
    if not current_user.has_permission("attendance:write"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to record attendance",
        )

    result = await service.check_in(
        person_id=request.person_id,
        confidence=request.confidence_threshold,
    )

    if result["success"]:
        return SuccessResponse(
            data=CheckInResponse(
                success=True,
                person_id=result["person_id"],
                person_name=result["person_name"],
                check_in_time=result["check_in_time"],
                confidence=result["confidence"],
                message="Check-in successful",
                error=None,
            )
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Check-in failed"),
        )


@router.post("/check-out", response_model=SuccessResponse[CheckOutResponse])
async def check_out(
    request: CheckOutRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: AttendanceService = Depends(get_attendance_service),
) -> SuccessResponse[CheckOutResponse]:
    """Record check-out for a person."""
    if not current_user.has_permission("attendance:write"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to record attendance",
        )

    result = await service.check_out(person_id=request.person_id)

    if result["success"]:
        return SuccessResponse(
            data=CheckOutResponse(
                success=True,
                person_id=result["person_id"],
                person_name=result["person_name"],
                check_out_time=result["check_out_time"],
                duration_minutes=result.get("duration_minutes", 0),
                message="Check-out successful",
                error=None,
            )
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Check-out failed"),
        )


# ============================================================================
# Attendance Query Endpoints
# ============================================================================


@router.get("", response_model=PaginatedResponse[AttendanceResponse])
async def get_attendance(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    person_id: Optional[str] = Query(None, description="Filter by person"),
    from_date: Optional[datetime] = Query(None, description="From date"),
    to_date: Optional[datetime] = Query(None, description="To date"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: CurrentUser = Depends(get_current_user),
    service: AttendanceService = Depends(get_attendance_service),
) -> PaginatedResponse[AttendanceResponse]:
    """Get attendance records."""
    if not current_user.has_permission("attendance:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view attendance",
        )

    skip = (page - 1) * page_size

    if person_id:
        records = await service.get_person_attendance(
            person_id,
            from_date=from_date,
            to_date=to_date,
            limit=page_size + skip,
            offset=0,
        )
    elif from_date and to_date:
        records = await service.get_daily_attendance(from_date)
    else:
        records = []

    # Apply pagination
    paginated = records[skip : skip + page_size]
    total = len(records)
    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        data=[
            AttendanceResponse(
                id=r.id,
                person_id=r.person_id,
                attendance_date=r.attendance_date,
                check_in_time=r.check_in_time,
                check_in_confidence=r.check_in_confidence,
                check_in_source=r.check_in_source,
                check_out_time=r.check_out_time,
                check_out_confidence=r.check_out_confidence,
                check_out_source=r.check_out_source,
                duration_minutes=r.duration_minutes,
                status=r.status,
                is_manual=r.is_manual,
                createdAt=r.created_at,
                updatedAt=r.updated_at,
            )
            for r in paginated
        ],
        meta=PaginationMeta(page=page, pageSize=page_size, total=total, totalPages=total_pages),
    )


@router.get("/{person_id}", response_model=PaginatedResponse[AttendanceResponse])
async def get_person_attendance(
    person_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(30, ge=1, le=100, description="Page size"),
    from_date: Optional[datetime] = Query(None, description="From date"),
    to_date: Optional[datetime] = Query(None, description="To date"),
    current_user: CurrentUser = Depends(get_current_user),
    service: AttendanceService = Depends(get_attendance_service),
) -> PaginatedResponse[AttendanceResponse]:
    """Get attendance for a specific person."""
    if not current_user.has_permission("attendance:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view attendance",
        )

    skip = (page - 1) * page_size

    try:
        records = await service.get_person_attendance(
            person_id,
            from_date=from_date,
            to_date=to_date,
            limit=page_size + skip,
            offset=0,
        )

        paginated = records[skip : skip + page_size]
        total = len(records)
        total_pages = (total + page_size - 1) // page_size

        return PaginatedResponse(
            data=[
                AttendanceResponse(
                    id=r.id,
                    person_id=r.person_id,
                    attendance_date=r.attendance_date,
                    check_in_time=r.check_in_time,
                    check_in_confidence=r.check_in_confidence,
                    check_in_source=r.check_in_source,
                    check_out_time=r.check_out_time,
                    check_out_confidence=r.check_out_confidence,
                    check_out_source=r.check_out_source,
                    duration_minutes=r.duration_minutes,
                    status=r.status,
                    is_manual=r.is_manual,
                    createdAt=r.created_at,
                    updatedAt=r.updated_at,
                )
                for r in paginated
            ],
            meta=PaginationMeta(page=page, pageSize=page_size, total=total, totalPages=total_pages),
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# Statistics & Reports
# ============================================================================


@router.get("/reports/daily", response_model=SuccessResponse[dict])
async def get_daily_attendance_report(
    date: Optional[datetime] = Query(None, description="Date (default: today)"),
    current_user: CurrentUser = Depends(get_current_user),
    service: AttendanceService = Depends(get_attendance_service),
) -> SuccessResponse[dict]:
    """Get daily attendance report."""
    if not current_user.has_permission("attendance:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view reports",
        )

    date = date or datetime.utcnow()
    report = await service.get_daily_attendance_summary(date)

    return SuccessResponse(data=report)


@router.get("/{person_id}/statistics", response_model=SuccessResponse[AttendanceStatistics])
async def get_person_attendance_stats(
    person_id: str,
    from_date: Optional[datetime] = Query(None, description="From date"),
    to_date: Optional[datetime] = Query(None, description="To date"),
    current_user: CurrentUser = Depends(get_current_user),
    service: AttendanceService = Depends(get_attendance_service),
) -> SuccessResponse[AttendanceStatistics]:
    """Get attendance statistics for a person."""
    if not current_user.has_permission("attendance:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view statistics",
        )

    try:
        stats = await service.get_person_attendance_stats(person_id, from_date, to_date)

        return SuccessResponse(
            data=AttendanceStatistics(
                total_working_days=stats["total_working_days"],
                days_present=stats["days_present"],
                days_absent=stats["days_absent"],
                days_late=stats["days_late"],
                days_early_leave=stats.get("days_early_leave", 0),
                presence_percentage=stats["presence_percentage"],
                average_check_in_delay_minutes=None,
            )
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# Status Endpoints
# ============================================================================


@router.get("/status/{person_id}", response_model=SuccessResponse[PersonCurrentStatus])
async def get_person_status(
    person_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: AttendanceService = Depends(get_attendance_service),
) -> SuccessResponse[PersonCurrentStatus]:
    """Get current check-in status for a person."""
    if not current_user.has_permission("attendance:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view status",
        )

    status_data = await service.get_current_check_in_status(person_id)

    return SuccessResponse(
        data=PersonCurrentStatus(
            person_id=status_data["person_id"],
            person_name="",  # Would need to fetch from person service
            checked_in=status_data["checked_in"],
            check_in_time=status_data.get("check_in_time"),
            current_duration_minutes=status_data.get("current_duration_minutes"),
            last_detection_time=None,
            last_detection_location=None,
        )
    )
