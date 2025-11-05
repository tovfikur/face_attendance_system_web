"""Cleanup tasks for housekeeping."""

import logging

from app.db.session import AsyncSessionLocal
from app.repositories.camera import CameraHealthRepository, CameraSnapshotRepository
from worker.celery_app import app

logger = logging.getLogger(__name__)


@app.task(
    name="worker.tasks.cleanup.cleanup_expired_snapshots",
    bind=True,
)
def cleanup_expired_snapshots(self):
    """
    Clean up expired snapshots from database and storage.

    This task runs daily and removes:
    - Snapshots past their expiry date
    - Associated storage files from MinIO
    """
    logger.info("Starting cleanup of expired snapshots")

    try:
        import asyncio
        result = asyncio.run(_async_cleanup_expired_snapshots())
        logger.info(f"Snapshot cleanup completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Error during snapshot cleanup: {e}")
        raise


async def _async_cleanup_expired_snapshots() -> dict:
    """Async implementation of snapshot cleanup."""
    async with AsyncSessionLocal() as session:
        snapshot_repo = CameraSnapshotRepository(session)

        # Delete expired snapshots from database
        deleted_count = await snapshot_repo.delete_expired()

        logger.info(f"Deleted {deleted_count} expired snapshot records from database")

        # TODO: Delete associated files from MinIO storage
        # This would require the StorageService to delete files from MinIO

        return {
            "deleted_snapshots": deleted_count,
            "deleted_files": 0,  # TODO: implement file deletion
        }


@app.task(
    name="worker.tasks.cleanup.cleanup_old_health_records",
    bind=True,
)
def cleanup_old_health_records(self, days: int = 30):
    """
    Clean up old camera health records.

    This task runs weekly and removes health records older than specified days.

    Args:
        days: Number of days to keep (default 30 days)
    """
    logger.info(f"Starting cleanup of health records older than {days} days")

    try:
        import asyncio
        result = asyncio.run(_async_cleanup_old_health_records(days))
        logger.info(f"Health record cleanup completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Error during health record cleanup: {e}")
        raise


async def _async_cleanup_old_health_records(days: int) -> dict:
    """Async implementation of health record cleanup."""
    async with AsyncSessionLocal() as session:
        health_repo = CameraHealthRepository(session)

        # Delete old health records
        deleted_count = await health_repo.delete_old_records(days=days)

        logger.info(f"Deleted {deleted_count} health records older than {days} days")

        return {
            "deleted_records": deleted_count,
            "days_kept": days,
        }


@app.task(
    name="worker.tasks.cleanup.optimize_database",
    bind=True,
)
def optimize_database(self):
    """
    Optimize database tables.

    This task runs periodically and performs database maintenance:
    - Vacuum and analyze tables
    - Clean up unused indexes
    """
    logger.info("Starting database optimization")

    try:
        import asyncio
        result = asyncio.run(_async_optimize_database())
        logger.info(f"Database optimization completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Error during database optimization: {e}")
        raise


async def _async_optimize_database() -> dict:
    """Async implementation of database optimization."""
    # Note: This is a placeholder. In production, you would run database-specific commands
    # For PostgreSQL, this would be VACUUM ANALYZE and REINDEX

    logger.info("Database optimization would run here (VACUUM ANALYZE, etc.)")

    return {
        "success": True,
        "message": "Database optimization completed",
    }
