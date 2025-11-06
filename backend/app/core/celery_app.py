"""
Celery application configuration and initialization.

This module sets up Celery with Redis as broker and backend,
along with task routing and configuration.
"""

from __future__ import annotations

from celery import Celery, Task
from celery.schedules import crontab

from app.core.config import settings

# Create Celery app instance
celery_app = Celery(
    "face_attendance_system",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Configure Celery
celery_app.conf.update(
    # Task configuration
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    accept_content=["json"],
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=True,

    # Task execution
    task_track_started=True,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,

    # Worker configuration
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,

    # Result backend configuration
    result_expires=3600,  # Results expire after 1 hour
    result_extended=True,

    # Task routing
    task_routes={
        "app.tasks.detection.*": {"queue": "detection"},
        "app.tasks.camera.*": {"queue": "camera"},
        "app.tasks.export.*": {"queue": "export"},
        "app.tasks.sync.*": {"queue": "sync"},
        "app.tasks.notification.*": {"queue": "notification"},
    },

    # Queues definition
    task_queues={
        "celery": {"exchange": "celery", "routing_key": "celery"},
        "detection": {"exchange": "detection", "routing_key": "detection"},
        "camera": {"exchange": "camera", "routing_key": "camera"},
        "export": {"exchange": "export", "routing_key": "export"},
        "sync": {"exchange": "sync", "routing_key": "sync"},
        "notification": {"exchange": "notification", "routing_key": "notification"},
    },

    # Periodic tasks (beat scheduler)
    beat_schedule={
        "cleanup-old-detections": {
            "task": "app.tasks.detection.cleanup_old_detections",
            "schedule": crontab(hour=2, minute=0),  # Run at 2 AM daily
        },
        "cleanup-old-sessions": {
            "task": "app.tasks.auth.cleanup_expired_sessions",
            "schedule": crontab(hour=3, minute=0),  # Run at 3 AM daily
        },
        "health-check-cameras": {
            "task": "app.tasks.camera.health_check_all",
            "schedule": crontab(minute="*/5"),  # Run every 5 minutes
        },
        "collect-system-metrics": {
            "task": "app.tasks.monitoring.collect_metrics",
            "schedule": crontab(minute="*"),  # Run every minute
        },
    },
)


class CallbackTask(Task):
    """Task class with callbacks."""

    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True


celery_app.Task = CallbackTask


@celery_app.task(bind=True)
def debug_task(self) -> str:
    """Debug task for testing Celery connectivity."""
    return f"Request: {self.request!r}"


__all__ = [
    "celery_app",
    "CallbackTask",
    "debug_task",
]
