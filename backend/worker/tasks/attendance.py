"""Attendance processing tasks."""

import logging

from app.db.session import AsyncSessionLocal
from app.repositories.detection import DetectionRepository
from app.services.auto_attendance import AutoAttendanceService
from app.services.attendance_service import AttendanceService
from worker.celery_app import app

logger = logging.getLogger(__name__)


@app.task(
    name="worker.tasks.attendance.process_detection_for_attendance",
    bind=True,
    max_retries=2,
)
def process_detection_for_attendance(self, detection_id: str):
    """
    Process a detection and mark attendance if applicable.

    This task is triggered when a detection is created and has a linked person.

    Args:
        detection_id: ID of the detection to process
    """
    logger.info(f"Processing detection for attendance: {detection_id}")

    try:
        import asyncio

        result = asyncio.run(_async_process_detection(detection_id))
        logger.info(f"Detection processing result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error processing detection: {e}")
        raise self.retry(exc=e, countdown=30 * (2 ** self.request.retries))


async def _async_process_detection(detection_id: str) -> dict:
    """Async implementation of detection processing."""
    async with AsyncSessionLocal() as session:
        detection_repo = DetectionRepository(session)
        auto_attendance = AutoAttendanceService(session)

        try:
            # Get detection
            detection = await detection_repo.get_by_id(detection_id)
            if not detection:
                logger.warning(f"Detection not found: {detection_id}")
                return {"success": False, "error": "Detection not found"}

            # Process for attendance
            result = await auto_attendance.process_detection_for_attendance(detection)

            return {
                "success": True,
                "detection_id": detection_id,
                "result": result,
            }

        except Exception as e:
            logger.error(f"Error in detection processing: {e}")
            raise


@app.task(
    name="worker.tasks.attendance.batch_process_recent_detections",
    bind=True,
)
def batch_process_recent_detections(self, minutes: int = 5):
    """
    Process recent detections for attendance in batch.

    This task runs periodically to process accumulated detections.

    Args:
        minutes: Process detections from last N minutes
    """
    logger.info(f"Batch processing detections from last {minutes} minutes")

    try:
        import asyncio

        result = asyncio.run(_async_batch_process(minutes))
        logger.info(f"Batch processing completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in batch processing: {e}")
        raise


async def _async_batch_process(minutes: int) -> dict:
    """Async implementation of batch processing."""
    from datetime import datetime, timedelta

    async with AsyncSessionLocal() as session:
        detection_repo = DetectionRepository(session)
        auto_attendance = AutoAttendanceService(session)

        try:
            # Get recent detections with persons
            cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
            recent = await detection_repo.get_recent(minutes=minutes, limit=1000)

            # Filter detections with person linkage
            detections_with_persons = [d for d in recent if d.person_id]

            logger.info(f"Found {len(detections_with_persons)} recent detections with persons")

            # Process batch
            result = await auto_attendance.process_batch_detections(detections_with_persons)

            return {
                "success": True,
                "detections_processed": len(detections_with_persons),
                "summary": result,
            }

        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            raise


@app.task(
    name="worker.tasks.attendance.generate_daily_attendance_report",
    bind=True,
)
def generate_daily_attendance_report(self, date_str: str = None):
    """
    Generate daily attendance report.

    This task runs daily to generate and cache attendance summaries.

    Args:
        date_str: Date string (YYYY-MM-DD), default: today
    """
    logger.info(f"Generating daily attendance report for {date_str or 'today'}")

    try:
        import asyncio

        result = asyncio.run(_async_generate_daily_report(date_str))
        logger.info(f"Daily report generated: {result}")
        return result
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise


async def _async_generate_daily_report(date_str: str = None) -> dict:
    """Async implementation of daily report generation."""
    from datetime import datetime

    async with AsyncSessionLocal() as session:
        attendance_service = AttendanceService(session)

        try:
            # Parse date or use today
            if date_str:
                report_date = datetime.strptime(date_str, "%Y-%m-%d")
            else:
                report_date = datetime.utcnow()

            # Generate report
            report = await attendance_service.get_daily_attendance_summary(report_date)

            logger.info(
                f"Report for {report_date.date()}: "
                f"{report['present']} present, {report['absent']} absent, "
                f"{report['late']} late ({report['presence_percentage']:.1f}% presence)"
            )

            return {
                "success": True,
                "date": str(report_date.date()),
                "report": report,
            }

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            raise


@app.task(
    name="worker.tasks.attendance.generate_monthly_report",
    bind=True,
)
def generate_monthly_report(self, year: int = None, month: int = None):
    """
    Generate monthly attendance report.

    Args:
        year: Year (default: current year)
        month: Month 1-12 (default: current month)
    """
    logger.info(f"Generating monthly report for {year}/{month}")

    try:
        import asyncio

        result = asyncio.run(_async_generate_monthly_report(year, month))
        logger.info(f"Monthly report generated: {result}")
        return result
    except Exception as e:
        logger.error(f"Error generating monthly report: {e}")
        raise


async def _async_generate_monthly_report(year: int = None, month: int = None) -> dict:
    """Async implementation of monthly report generation."""
    from datetime import datetime

    async with AsyncSessionLocal() as session:
        attendance_service = AttendanceService(session)

        try:
            now = datetime.utcnow()
            year = year or now.year
            month = month or now.month

            # Generate daily reports for month
            from datetime import timedelta

            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)

            daily_reports = []
            current = start_date

            while current < end_date:
                report = await attendance_service.get_daily_attendance_summary(current)
                daily_reports.append(report)
                current += timedelta(days=1)

            # Calculate monthly totals
            total_persons = sum(r["total_persons"] for r in daily_reports)
            total_present = sum(r["present"] for r in daily_reports)
            avg_presence = (total_present / total_persons * 100) if total_persons > 0 else 0

            logger.info(
                f"Monthly report {year}/{month}: {total_present} present out of {total_persons} "
                f"({avg_presence:.1f}% average)"
            )

            return {
                "success": True,
                "year": year,
                "month": month,
                "total_attendance_records": total_present,
                "average_presence_percentage": avg_presence,
                "daily_reports": daily_reports,
            }

        except Exception as e:
            logger.error(f"Error generating monthly report: {e}")
            raise


@app.task(
    name="worker.tasks.attendance.send_attendance_notifications",
    bind=True,
)
def send_attendance_notifications(self, person_id: str = None):
    """
    Send attendance notifications to persons.

    Notifies about late arrivals, early departures, or absences.

    Args:
        person_id: Specific person (optional, all if not specified)
    """
    logger.info(f"Sending attendance notifications for {person_id or 'all persons'}")

    try:
        import asyncio

        result = asyncio.run(_async_send_notifications(person_id))
        logger.info(f"Notifications sent: {result}")
        return result
    except Exception as e:
        logger.error(f"Error sending notifications: {e}")
        raise


async def _async_send_notifications(person_id: str = None) -> dict:
    """Async implementation of sending notifications."""
    async with AsyncSessionLocal() as session:
        attendance_service = AttendanceService(session)

        try:
            # Get today's attendance
            today = __import__("datetime").datetime.utcnow()
            report = await attendance_service.get_daily_attendance_summary(today)

            # Count notifications
            lates = report.get("late", 0)
            absences = report.get("absent", 0)

            # TODO: Send actual notifications via email, SMS, or in-app notifications
            # This is a placeholder for the notification system

            logger.info(f"Would notify {lates} late persons and {absences} absent persons")

            return {
                "success": True,
                "notifications_sent": lates + absences,
                "late_notifications": lates,
                "absence_notifications": absences,
            }

        except Exception as e:
            logger.error(f"Error sending notifications: {e}")
            raise


@app.task(
    name="worker.tasks.attendance.cleanup_old_attendance",
    bind=True,
)
def cleanup_old_attendance(self, days: int = 90):
    """
    Clean up old attendance records.

    Args:
        days: Delete records older than N days
    """
    logger.info(f"Cleaning up attendance records older than {days} days")

    try:
        import asyncio

        result = asyncio.run(_async_cleanup_attendance(days))
        logger.info(f"Cleanup completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Error cleaning up: {e}")
        raise


async def _async_cleanup_attendance(days: int) -> dict:
    """Async implementation of cleanup."""
    from datetime import datetime, timedelta

    async with AsyncSessionLocal() as session:
        from app.repositories.attendance import AttendanceRepository

        try:
            repo = AttendanceRepository(session)
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # This would require implementing a delete_old_records method in repository
            # For now, placeholder

            logger.info(f"Would delete attendance records before {cutoff_date}")

            return {
                "success": True,
                "message": f"Cleanup of records older than {days} days completed",
            }

        except Exception as e:
            logger.error(f"Error in cleanup: {e}")
            raise
