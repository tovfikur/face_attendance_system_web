"""Attendance service for attendance tracking and reporting."""

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationError
from app.models.attendance import Attendance, AttendanceSession
from app.repositories.attendance import (
    AttendanceRepository,
    AttendanceSessionRepository,
)
from app.services.person_service import PersonService

logger = logging.getLogger(__name__)


class AttendanceService:
    """Service for attendance tracking and management."""

    # Duplicate detection window (minutes)
    DUPLICATE_CHECK_WINDOW = 5

    def __init__(self, db: AsyncSession):
        """Initialize attendance service."""
        self.db = db
        self.repo = AttendanceRepository(db)
        self.session_repo = AttendanceSessionRepository(db)
        self.person_service = PersonService(db)

    # =========================================================================
    # Check-in/Check-out Methods
    # =========================================================================

    async def check_in(
        self,
        person_id: str,
        check_in_time: Optional[datetime] = None,
        detection_id: Optional[str] = None,
        confidence: float = 1.0,
        camera_id: Optional[str] = None,
        is_manual: bool = False,
    ) -> dict:
        """
        Record check-in for a person.

        Args:
            person_id: Person ID
            check_in_time: Check-in time (default: now)
            detection_id: Source detection ID
            confidence: Detection confidence
            camera_id: Camera ID where detected
            is_manual: Is manual entry

        Returns:
            Check-in result
        """
        try:
            # Verify person exists
            person = await self.person_service.get_person(person_id)

            check_in_time = check_in_time or datetime.utcnow()
            attendance_date = check_in_time.replace(hour=0, minute=0, second=0, microsecond=0)

            # Check for duplicate check-in (within window)
            existing = await self.repo.get_by_person_and_date(person_id, attendance_date)

            if existing and existing.check_in_time:
                time_diff = (check_in_time - existing.check_in_time).total_seconds() / 60
                if time_diff < self.DUPLICATE_CHECK_WINDOW:
                    logger.warning(f"Duplicate check-in detected for {person_id}")
                    return {
                        "success": False,
                        "error": "Duplicate check-in detected",
                        "attendance_id": existing.id,
                    }

            # Create or update attendance record
            if existing:
                # Update existing record
                updated = await self.repo.update(
                    existing.id,
                    check_in_time=check_in_time,
                    check_in_detection_id=detection_id,
                    check_in_confidence=confidence,
                    check_in_camera_id=camera_id,
                    check_in_source="manual" if is_manual else "detection",
                    status="present",
                )
                attendance = updated
                is_new = False
            else:
                # Create new record
                attendance_id = str(uuid4())
                attendance = await self.repo.create(
                    attendance_id=attendance_id,
                    person_id=person_id,
                    attendance_date=attendance_date,
                    check_in_time=check_in_time,
                    check_in_detection_id=detection_id,
                    check_in_confidence=confidence,
                    check_in_camera_id=camera_id,
                    check_in_source="manual" if is_manual else "detection",
                    status="present",
                )
                is_new = True

            logger.info(f"Check-in recorded for {person_id} at {check_in_time}")

            return {
                "success": True,
                "attendance_id": attendance.id,
                "person_id": person_id,
                "person_name": f"{person.first_name} {person.last_name}",
                "check_in_time": check_in_time,
                "is_new": is_new,
                "confidence": confidence,
            }

        except NotFoundError as e:
            logger.error(f"Error checking in: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def check_out(
        self,
        person_id: str,
        check_out_time: Optional[datetime] = None,
        detection_id: Optional[str] = None,
        confidence: float = 1.0,
        camera_id: Optional[str] = None,
        is_manual: bool = False,
    ) -> dict:
        """
        Record check-out for a person.

        Args:
            person_id: Person ID
            check_out_time: Check-out time (default: now)
            detection_id: Source detection ID
            confidence: Detection confidence
            camera_id: Camera ID where detected
            is_manual: Is manual entry

        Returns:
            Check-out result
        """
        try:
            # Verify person exists
            person = await self.person_service.get_person(person_id)

            check_out_time = check_out_time or datetime.utcnow()
            attendance_date = check_out_time.replace(hour=0, minute=0, second=0, microsecond=0)

            # Get today's attendance
            existing = await self.repo.get_by_person_and_date(person_id, attendance_date)

            if not existing or not existing.check_in_time:
                logger.warning(f"No check-in found for {person_id} on {attendance_date}")
                return {
                    "success": False,
                    "error": "No check-in record found for today",
                }

            # Check for duplicate check-out
            if existing.check_out_time:
                time_diff = (check_out_time - existing.check_out_time).total_seconds() / 60
                if time_diff < self.DUPLICATE_CHECK_WINDOW:
                    logger.warning(f"Duplicate check-out detected for {person_id}")
                    return {
                        "success": False,
                        "error": "Duplicate check-out detected",
                        "attendance_id": existing.id,
                    }

            # Calculate duration
            duration = check_out_time - existing.check_in_time
            duration_minutes = int(duration.total_seconds() / 60)

            # Update attendance record
            updated = await self.repo.update(
                existing.id,
                check_out_time=check_out_time,
                check_out_detection_id=detection_id,
                check_out_confidence=confidence,
                check_out_camera_id=camera_id,
                check_out_source="manual" if is_manual else "detection",
                duration_minutes=duration_minutes,
            )

            logger.info(f"Check-out recorded for {person_id} at {check_out_time}")

            return {
                "success": True,
                "attendance_id": updated.id,
                "person_id": person_id,
                "person_name": f"{person.first_name} {person.last_name}",
                "check_in_time": updated.check_in_time,
                "check_out_time": check_out_time,
                "duration_minutes": duration_minutes,
                "confidence": confidence,
            }

        except NotFoundError as e:
            logger.error(f"Error checking out: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    # =========================================================================
    # Attendance Query Methods
    # =========================================================================

    async def get_attendance(self, attendance_id: str) -> Attendance:
        """Get attendance record by ID."""
        attendance = await self.repo.get_by_id(attendance_id)
        if not attendance:
            raise NotFoundError(f"Attendance record {attendance_id} not found")
        return attendance

    async def get_person_attendance(
        self,
        person_id: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Attendance]:
        """Get attendance records for a person."""
        if not from_date:
            from_date = datetime.utcnow() - timedelta(days=30)
        if not to_date:
            to_date = datetime.utcnow()

        return await self.repo.get_by_person(
            person_id,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            offset=offset,
        )

    async def get_daily_attendance(
        self,
        attendance_date: datetime,
        limit: int = 1000,
    ) -> list[Attendance]:
        """Get all attendance for a specific date."""
        date_start = attendance_date.replace(hour=0, minute=0, second=0, microsecond=0)
        date_end = date_start + timedelta(days=1)

        return await self.repo.get_by_date_range(date_start, date_end, limit=limit)

    async def get_current_check_in_status(self, person_id: str) -> dict:
        """Get current check-in status for a person."""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        attendance = await self.repo.get_by_person_and_date(person_id, today_start)

        if not attendance:
            return {
                "person_id": person_id,
                "checked_in": False,
                "check_in_time": None,
                "current_duration_minutes": None,
                "status": "not_checked_in",
            }

        if not attendance.check_in_time:
            return {
                "person_id": person_id,
                "checked_in": False,
                "check_in_time": None,
                "current_duration_minutes": None,
                "status": "not_checked_in",
            }

        if attendance.check_out_time:
            return {
                "person_id": person_id,
                "checked_in": False,
                "check_in_time": attendance.check_in_time,
                "check_out_time": attendance.check_out_time,
                "duration_minutes": attendance.duration_minutes,
                "status": "checked_out",
            }

        # Calculate current duration
        current_duration = datetime.utcnow() - attendance.check_in_time
        current_duration_minutes = int(current_duration.total_seconds() / 60)

        return {
            "person_id": person_id,
            "checked_in": True,
            "check_in_time": attendance.check_in_time,
            "current_duration_minutes": current_duration_minutes,
            "status": "checked_in",
        }

    # =========================================================================
    # Attendance Statistics Methods
    # =========================================================================

    async def get_person_attendance_stats(
        self,
        person_id: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> dict:
        """Get attendance statistics for a person."""
        if not from_date:
            from_date = datetime.utcnow() - timedelta(days=30)
        if not to_date:
            to_date = datetime.utcnow()

        records = await self.repo.get_by_person(
            person_id,
            from_date=from_date,
            to_date=to_date,
            limit=1000,
        )

        # Count by status
        status_count = {}
        total_duration = 0

        for record in records:
            status = record.status
            status_count[status] = status_count.get(status, 0) + 1
            if record.duration_minutes:
                total_duration += record.duration_minutes

        days_diff = (to_date - from_date).days
        working_days = days_diff  # Simplified (doesn't account for weekends)

        return {
            "person_id": person_id,
            "from_date": from_date,
            "to_date": to_date,
            "total_working_days": working_days,
            "total_attendance_records": len(records),
            "status_breakdown": status_count,
            "days_present": status_count.get("present", 0),
            "days_absent": status_count.get("absent", 0),
            "days_late": status_count.get("late", 0),
            "presence_percentage": (status_count.get("present", 0) / working_days * 100) if working_days > 0 else 0,
            "total_duration_minutes": total_duration,
            "average_duration_minutes": total_duration // len(records) if records else 0,
        }

    async def get_daily_attendance_summary(self, attendance_date: datetime) -> dict:
        """Get daily attendance summary."""
        records = await self.get_daily_attendance(attendance_date)

        status_count = {}
        for record in records:
            status = record.status
            status_count[status] = status_count.get(status, 0) + 1

        total = len(records)
        present = status_count.get("present", 0)

        return {
            "date": attendance_date,
            "total_persons": total,
            "present": present,
            "absent": status_count.get("absent", 0),
            "late": status_count.get("late", 0),
            "early_leave": status_count.get("early_leave", 0),
            "presence_percentage": (present / total * 100) if total > 0 else 0,
            "status_breakdown": status_count,
        }

    # =========================================================================
    # Attendance Session Management
    # =========================================================================

    async def create_session(
        self,
        name: str,
        start_time,
        end_time,
        expected_duration_minutes: int,
        grace_period_minutes: int = 5,
    ) -> AttendanceSession:
        """Create attendance session."""
        session_id = str(uuid4())
        session = await self.session_repo.create(
            session_id=session_id,
            name=name,
            start_time=start_time,
            end_time=end_time,
            expected_duration_minutes=expected_duration_minutes,
            grace_period_minutes=grace_period_minutes,
        )
        logger.info(f"Created attendance session: {session_id}")
        return session

    async def get_session(self, session_id: str) -> AttendanceSession:
        """Get attendance session."""
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise NotFoundError(f"Session {session_id} not found")
        return session

    async def list_sessions(self) -> list[AttendanceSession]:
        """List all attendance sessions."""
        return await self.session_repo.get_all()

    # =========================================================================
    # Utility Methods
    # =========================================================================

    async def mark_attendance_status(
        self,
        person_id: str,
        attendance_date: datetime,
        status: str,
        reason: Optional[str] = None,
    ) -> Attendance:
        """Manually mark attendance status."""
        date_start = attendance_date.replace(hour=0, minute=0, second=0, microsecond=0)

        # Get or create attendance record
        existing = await self.repo.get_by_person_and_date(person_id, date_start)

        if existing:
            updated = await self.repo.update(
                existing.id,
                status=status,
                notes=reason,
            )
            return updated
        else:
            attendance_id = str(uuid4())
            attendance = await self.repo.create(
                attendance_id=attendance_id,
                person_id=person_id,
                attendance_date=date_start,
                status=status,
                notes=reason,
                is_manual=True,
            )
            return attendance
