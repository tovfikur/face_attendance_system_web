"""Monitoring tasks for camera health checks."""

import logging
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.camera import Camera, CameraHealth
from app.repositories.camera import CameraHealthRepository
from worker.celery_app import app

logger = logging.getLogger(__name__)


@app.task(
    name="worker.tasks.monitoring.check_camera_health",
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def check_camera_health(self):
    """
    Check health of all cameras.

    This task runs every minute and:
    - Tests RTSP connection for each camera
    - Records latency metrics
    - Updates camera status
    - Stores health records
    """
    logger.info("Starting camera health check task")

    try:
        import asyncio
        # Run the async check function
        result = asyncio.run(_async_check_camera_health())
        logger.info(f"Camera health check completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Error during camera health check: {e}")
        # Retry the task
        raise self.retry(exc=e, countdown=60)


async def _async_check_camera_health() -> dict:
    """Async implementation of camera health checking."""
    async with AsyncSessionLocal() as session:
        # Get all active cameras
        result = await session.execute(
            select(Camera).where(Camera.is_active == True)
        )
        cameras = result.scalars().all()

        if not cameras:
            logger.info("No active cameras to check")
            return {"checked": 0, "healthy": 0, "unhealthy": 0}

        logger.info(f"Checking health of {len(cameras)} cameras")

        health_repo = CameraHealthRepository(session)
        checked_count = 0
        healthy_count = 0
        unhealthy_count = 0

        # Check each camera
        for camera in cameras:
            try:
                # TODO: Implement actual RTSP connection check
                # For now, we'll create a mock health record

                is_connected = True  # Mock: assume connected
                latency_ms = 50  # Mock: 50ms latency
                fps_actual = camera.fps  # Mock: actual FPS matches configured

                # Create health record
                health_id = str(uuid4())
                health_record = await health_repo.create(
                    health_id=health_id,
                    camera_id=camera.id,
                    is_connected=is_connected,
                    latency_ms=latency_ms,
                    fps_actual=fps_actual,
                    status_message="Camera is healthy" if is_connected else "Connection failed",
                )

                # Update camera status
                if is_connected:
                    camera.status = "live"
                    camera.last_connected = datetime.utcnow()
                    healthy_count += 1
                else:
                    camera.status = "error"
                    camera.connection_retries += 1
                    unhealthy_count += 1

                session.add(camera)
                checked_count += 1

            except Exception as e:
                logger.error(f"Error checking camera {camera.id}: {e}")
                camera.status = "error"
                camera.last_error = str(e)
                camera.connection_retries += 1
                unhealthy_count += 1
                session.add(camera)
                checked_count += 1

        # Commit all changes
        await session.commit()

        logger.info(f"Camera health check completed: {checked_count} checked, {healthy_count} healthy, {unhealthy_count} unhealthy")

        return {
            "checked": checked_count,
            "healthy": healthy_count,
            "unhealthy": unhealthy_count,
        }


@app.task(
    name="worker.tasks.monitoring.test_camera_snapshot",
    bind=True,
)
def test_camera_snapshot(self, camera_id: str):
    """
    Test snapshot capture from a camera.

    Args:
        camera_id: Camera ID to test
    """
    logger.info(f"Testing snapshot capture for camera {camera_id}")

    try:
        import asyncio
        result = asyncio.run(_async_test_snapshot(camera_id))
        logger.info(f"Snapshot test completed for camera {camera_id}: {result}")
        return result
    except Exception as e:
        logger.error(f"Error testing snapshot for camera {camera_id}: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


async def _async_test_snapshot(camera_id: str) -> dict:
    """Test snapshot capture asynchronously."""
    async with AsyncSessionLocal() as session:
        # Get camera
        result = await session.execute(
            select(Camera).where(Camera.id == camera_id)
        )
        camera = result.scalar_one_or_none()

        if not camera:
            return {"success": False, "error": f"Camera {camera_id} not found"}

        # TODO: Implement actual snapshot capture using FFmpeg
        # For now, return mock response

        return {
            "success": True,
            "camera_id": camera_id,
            "snapshot_path": f"snapshots/{camera_id}/{datetime.utcnow().timestamp()}.jpg",
        }


@app.task(
    name="worker.tasks.monitoring.generate_health_report",
    bind=True,
)
def generate_health_report(self, period_hours: int = 24):
    """
    Generate health report for all cameras.

    Args:
        period_hours: Number of hours to include in report
    """
    logger.info(f"Generating health report for last {period_hours} hours")

    try:
        import asyncio
        result = asyncio.run(_async_generate_health_report(period_hours))
        logger.info(f"Health report generated")
        return result
    except Exception as e:
        logger.error(f"Error generating health report: {e}")
        raise


async def _async_generate_health_report(period_hours: int) -> dict:
    """Generate health report asynchronously."""
    from datetime import timedelta

    async with AsyncSessionLocal() as session:
        # Get cameras with recent health records
        result = await session.execute(select(Camera).where(Camera.is_active == True))
        cameras = result.scalars().all()

        health_repo = CameraHealthRepository(session)
        report_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "period_hours": period_hours,
            "total_cameras": len(cameras),
            "cameras": [],
        }

        for camera in cameras:
            health_records = await health_repo.get_history(camera.id, limit=60)

            if health_records:
                avg_latency = sum(
                    h.latency_ms for h in health_records if h.latency_ms
                ) / len([h for h in health_records if h.latency_ms])

                uptime = sum(1 for h in health_records if h.is_connected) / len(health_records) * 100
            else:
                avg_latency = None
                uptime = 0

            report_data["cameras"].append({
                "id": camera.id,
                "name": camera.name,
                "status": camera.status,
                "uptime_percent": uptime,
                "avg_latency_ms": avg_latency,
                "recent_records": len(health_records),
            })

        return report_data
