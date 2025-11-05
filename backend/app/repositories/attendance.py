"""Attendance repositories for database operations."""

from datetime import datetime
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import Attendance, AttendanceSession


class AttendanceRepository:
    """Repository for attendance records."""

    def __init__(self, db: AsyncSession):
        """Initialize repository."""
        self.db = db

    async def create(self, attendance_id: str, **kwargs) -> Attendance:
        """Create attendance record."""
        attendance = Attendance(id=attendance_id, **kwargs)
        self.db.add(attendance)
        await self.db.commit()
        await self.db.refresh(attendance)
        return attendance

    async def get_by_id(self, attendance_id: str) -> Optional[Attendance]:
        """Get attendance by ID."""
        result = await self.db.execute(
            select(Attendance).where(Attendance.id == attendance_id)
        )
        return result.scalar_one_or_none()

    async def get_by_person_and_date(
        self,
        person_id: str,
        attendance_date: datetime,
    ) -> Optional[Attendance]:
        """Get attendance for person on specific date."""
        date_start = attendance_date.replace(hour=0, minute=0, second=0, microsecond=0)
        date_end = date_start.replace(hour=23, minute=59, second=59, microsecond=999999)

        result = await self.db.execute(
            select(Attendance).where(
                and_(
                    Attendance.person_id == person_id,
                    Attendance.attendance_date >= date_start,
                    Attendance.attendance_date <= date_end,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_person(
        self,
        person_id: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Attendance]:
        """Get attendance for a person."""
        query = select(Attendance).where(Attendance.person_id == person_id)

        if from_date:
            query = query.where(Attendance.attendance_date >= from_date)
        if to_date:
            query = query.where(Attendance.attendance_date <= to_date)

        query = query.order_by(Attendance.attendance_date.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_date_range(
        self,
        from_date: datetime,
        to_date: datetime,
        limit: int = 1000,
    ) -> list[Attendance]:
        """Get all attendance in date range."""
        result = await self.db.execute(
            select(Attendance)
            .where(
                and_(
                    Attendance.attendance_date >= from_date,
                    Attendance.attendance_date < to_date,
                )
            )
            .order_by(Attendance.attendance_date.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_status(
        self,
        status: str,
        limit: int = 100,
    ) -> list[Attendance]:
        """Get attendance by status."""
        result = await self.db.execute(
            select(Attendance)
            .where(Attendance.status == status)
            .order_by(Attendance.attendance_date.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_checked_in_persons(self) -> list[Attendance]:
        """Get all persons currently checked in."""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        result = await self.db.execute(
            select(Attendance).where(
                and_(
                    Attendance.attendance_date >= today_start,
                    Attendance.check_in_time != None,
                    Attendance.check_out_time == None,
                )
            )
        )
        return result.scalars().all()

    async def count_by_status(self, status: str, from_date: Optional[datetime] = None) -> int:
        """Count attendance by status."""
        query = select(func.count(Attendance.id)).where(Attendance.status == status)

        if from_date:
            query = query.where(Attendance.attendance_date >= from_date)

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def update(self, attendance_id: str, **kwargs) -> Optional[Attendance]:
        """Update attendance record."""
        attendance = await self.get_by_id(attendance_id)
        if not attendance:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(attendance, key):
                setattr(attendance, key, value)

        self.db.add(attendance)
        await self.db.commit()
        await self.db.refresh(attendance)
        return attendance

    async def delete(self, attendance_id: str) -> bool:
        """Delete attendance record."""
        attendance = await self.get_by_id(attendance_id)
        if not attendance:
            return False

        await self.db.delete(attendance)
        await self.db.commit()
        return True


class AttendanceSessionRepository:
    """Repository for attendance sessions."""

    def __init__(self, db: AsyncSession):
        """Initialize repository."""
        self.db = db

    async def create(self, session_id: str, **kwargs) -> AttendanceSession:
        """Create attendance session."""
        session = AttendanceSession(id=session_id, **kwargs)
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_by_id(self, session_id: str) -> Optional[AttendanceSession]:
        """Get session by ID."""
        result = await self.db.execute(
            select(AttendanceSession).where(AttendanceSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> list[AttendanceSession]:
        """Get all active sessions."""
        result = await self.db.execute(
            select(AttendanceSession)
            .where(AttendanceSession.is_active == True)
            .order_by(AttendanceSession.start_time)
        )
        return result.scalars().all()

    async def update(self, session_id: str, **kwargs) -> Optional[AttendanceSession]:
        """Update session."""
        session = await self.get_by_id(session_id)
        if not session:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(session, key):
                setattr(session, key, value)

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def delete(self, session_id: str) -> bool:
        """Delete session."""
        session = await self.get_by_id(session_id)
        if not session:
            return False

        await self.db.delete(session)
        await self.db.commit()
        return True
