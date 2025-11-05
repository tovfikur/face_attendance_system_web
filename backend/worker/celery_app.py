"""Celery application for background task processing."""

import logging
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create Celery app
app = Celery(
    "face_attendance_backend",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Configure Celery
app.conf.update(
    # Task configuration
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Result configuration
    result_expires=3600,
    result_backend_transport_options={
        "master_name": "mymaster" if settings.CELERY_RESULT_BACKEND.startswith("sentinel") else None,
    },
    # Task execution
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    # Worker configuration
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    # Routing configuration
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",
    # Beat schedule for periodic tasks
    beat_schedule={
        "check-camera-health-every-minute": {
            "task": "worker.tasks.monitoring.check_camera_health",
            "schedule": crontab(minute="*"),  # Every minute
            "args": (),
        },
        "cleanup-snapshots-daily": {
            "task": "worker.tasks.cleanup.cleanup_expired_snapshots",
            "schedule": crontab(hour=2, minute=0),  # 2 AM UTC daily
            "args": (),
        },
        "cleanup-health-records-weekly": {
            "task": "worker.tasks.cleanup.cleanup_old_health_records",
            "schedule": crontab(day_of_week=0, hour=3, minute=0),  # Sunday 3 AM UTC
            "args": (30,),  # Keep 30 days
        },
    },
)


# Autodiscover tasks from modules
app.autodiscover_tasks(
    [
        "worker.tasks.monitoring",
        "worker.tasks.cleanup",
    ],
    force=True,
)


@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery."""
    logger.info(f"Request: {self.request!r}")


if __name__ == "__main__":
    app.start()
