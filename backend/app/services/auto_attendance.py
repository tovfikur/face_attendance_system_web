"""Auto-attendance service for automatic attendance marking from detections."""

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.detection import Detection
from app.services.attendance_service import AttendanceService
from app.services.person_service import PersonService

logger = logging.getLogger(__name__)


class AutoAttendanceService:
    """Service for automatic attendance marking from detections."""

    # Confidence threshold for auto check-in (70%+)
    MIN_CONFIDENCE_FOR_AUTO_CHECK_IN = 0.7

    # Confidence threshold for manual review (60-70%)
    MIN_CONFIDENCE_FOR_REVIEW = 0.6

    # Time window to prevent duplicate check-ins (minutes)
    DUPLICATE_CHECK_WINDOW = 5

    def __init__(self, db: AsyncSession):
        """Initialize auto-attendance service."""
        self.db = db
        self.person_service = PersonService(db)
        self.attendance_service = AttendanceService(db)

    async def process_detection_for_attendance(
        self,
        detection: Detection,
    ) -> dict:
        """
        Process a detection and potentially mark attendance.

        Args:
            detection: Detection record

        Returns:
            Processing result with status and attendance info
        """
        try:
            # Only process detections with persons
            if not detection.person_id:
                return {
                    "processed": False,
                    "reason": "No person linked to detection",
                }

            # Check confidence threshold
            if detection.confidence < self.MIN_CONFIDENCE_FOR_REVIEW:
                return {
                    "processed": False,
                    "reason": f"Confidence below threshold ({detection.confidence:.2f})",
                }

            person_id = detection.person_id

            # Verify person exists
            try:
                person = await self.person_service.get_person(person_id)
            except Exception as e:
                logger.warning(f"Person {person_id} not found: {e}")
                return {
                    "processed": False,
                    "reason": f"Person {person_id} not found",
                }

            # Check if we should auto-mark attendance
            should_auto_mark = detection.confidence >= self.MIN_CONFIDENCE_FOR_AUTO_CHECK_IN

            if should_auto_mark:
                # Determine if this is check-in or check-out based on time of day
                detection_time = detection.created_at
                hour = detection_time.hour

                # Simple heuristic: before 12:00 = check-in, after 16:00 = check-out
                # Otherwise, don't auto-mark (requires manual decision)
                if hour < 12:
                    # Mark as check-in
                    result = await self.attendance_service.check_in(
                        person_id=person_id,
                        check_in_time=detection_time,
                        detection_id=detection.id,
                        confidence=detection.confidence,
                        camera_id=detection.camera_id,
                        is_manual=False,
                    )

                    if result["success"]:
                        logger.info(
                            f"Auto check-in for {person.first_name} {person.last_name} "
                            f"from detection {detection.id} (confidence: {detection.confidence:.2f})"
                        )
                        return {
                            "processed": True,
                            "action": "check_in",
                            "attendance_id": result["attendance_id"],
                            "person_name": result["person_name"],
                            "confidence": detection.confidence,
                        }
                    else:
                        logger.warning(f"Failed to record check-in: {result.get('error')}")
                        return {
                            "processed": False,
                            "reason": f"Failed to record check-in: {result.get('error')}",
                        }

                elif hour >= 16:
                    # Mark as check-out
                    result = await self.attendance_service.check_out(
                        person_id=person_id,
                        check_out_time=detection_time,
                        detection_id=detection.id,
                        confidence=detection.confidence,
                        camera_id=detection.camera_id,
                        is_manual=False,
                    )

                    if result["success"]:
                        logger.info(
                            f"Auto check-out for {person.first_name} {person.last_name} "
                            f"from detection {detection.id} (confidence: {detection.confidence:.2f})"
                        )
                        return {
                            "processed": True,
                            "action": "check_out",
                            "attendance_id": result["attendance_id"],
                            "person_name": result["person_name"],
                            "confidence": detection.confidence,
                        }
                    else:
                        logger.warning(f"Failed to record check-out: {result.get('error')}")
                        return {
                            "processed": False,
                            "reason": f"Failed to record check-out: {result.get('error')}",
                        }
                else:
                    # Mid-day detection, requires manual review
                    return {
                        "processed": False,
                        "reason": "Mid-day detection requires manual review",
                        "requires_review": True,
                        "confidence": detection.confidence,
                    }
            else:
                # Below auto-mark threshold, requires manual review
                return {
                    "processed": False,
                    "reason": "Confidence below auto-mark threshold",
                    "requires_review": True,
                    "confidence": detection.confidence,
                }

        except Exception as e:
            logger.error(f"Error processing detection for attendance: {e}")
            return {
                "processed": False,
                "reason": f"Error: {str(e)}",
                "error": str(e),
            }

    async def process_batch_detections(
        self,
        detections: list[Detection],
    ) -> dict:
        """
        Process multiple detections for attendance.

        Args:
            detections: List of detections

        Returns:
            Batch processing results
        """
        results = {
            "total_processed": 0,
            "auto_marked": 0,
            "requires_review": 0,
            "failed": 0,
            "details": [],
        }

        for detection in detections:
            result = await self.process_detection_for_attendance(detection)
            results["details"].append(result)

            if result["processed"]:
                results["auto_marked"] += 1
                results["total_processed"] += 1
            elif result.get("requires_review"):
                results["requires_review"] += 1
            else:
                results["failed"] += 1

        logger.info(
            f"Batch processing complete: {results['auto_marked']} auto-marked, "
            f"{results['requires_review']} require review, {results['failed']} failed"
        )

        return results

    async def get_pending_reviews(self) -> list[dict]:
        """
        Get detections that require manual review for attendance.

        Returns:
            List of detections pending manual review
        """
        pending = []

        # This would ideally query a "pending_review" table or flag
        # For now, return empty list as placeholder
        # In production, would fetch from database

        return pending

    async def manually_approve_attendance(
        self,
        detection_id: str,
        person_id: str,
        action: str,  # "check_in" or "check_out"
        timestamp: Optional[datetime] = None,
    ) -> dict:
        """
        Manually approve and record attendance for a detection.

        Args:
            detection_id: Detection ID
            person_id: Person ID
            action: Action type ("check_in" or "check_out")
            timestamp: Attendance timestamp (default: now)

        Returns:
            Result of attendance recording
        """
        try:
            timestamp = timestamp or datetime.utcnow()

            if action == "check_in":
                result = await self.attendance_service.check_in(
                    person_id=person_id,
                    check_in_time=timestamp,
                    detection_id=detection_id,
                    is_manual=True,
                )
                action_text = "check-in"
            elif action == "check_out":
                result = await self.attendance_service.check_out(
                    person_id=person_id,
                    check_out_time=timestamp,
                    detection_id=detection_id,
                    is_manual=True,
                )
                action_text = "check-out"
            else:
                return {
                    "success": False,
                    "error": f"Invalid action: {action}",
                }

            if result["success"]:
                logger.info(f"Manually approved {action_text} for {person_id} from detection {detection_id}")

            return result

        except Exception as e:
            logger.error(f"Error approving attendance: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def get_attendance_insights(self, person_id: str) -> dict:
        """
        Get insights about person's attendance patterns.

        Args:
            person_id: Person ID

        Returns:
            Attendance insights and patterns
        """
        try:
            person = await self.person_service.get_person(person_id)

            # Get 30-day stats
            from_date = datetime.utcnow() - timedelta(days=30)
            stats = await self.attendance_service.get_person_attendance_stats(
                person_id,
                from_date=from_date,
            )

            return {
                "person_id": person_id,
                "person_name": f"{person.first_name} {person.last_name}",
                "statistics": stats,
                "attendance_rate": stats["presence_percentage"],
                "trends": {
                    "is_frequent": stats["presence_percentage"] > 90,
                    "is_regular": 70 <= stats["presence_percentage"] <= 90,
                    "is_sporadic": 40 <= stats["presence_percentage"] < 70,
                    "is_rarely_present": stats["presence_percentage"] < 40,
                },
            }

        except Exception as e:
            logger.error(f"Error getting attendance insights: {e}")
            return {
                "error": str(e),
            }
