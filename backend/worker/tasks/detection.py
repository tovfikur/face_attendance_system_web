"""Detection processing tasks."""

import logging

from app.db.session import AsyncSessionLocal
from app.repositories.detection import (
    DetectionEventLogRepository,
    DetectionProcessingQueueRepository,
    DetectionRepository,
)
from app.services.detection_service import DetectionService
from worker.celery_app import app

logger = logging.getLogger(__name__)


@app.task(
    name="worker.tasks.detection.process_detection_frame",
    bind=True,
    max_retries=3,
)
def process_detection_frame(self, queue_id: str):
    """
    Process a detection frame from the queue.

    This task retrieves a pending frame from the queue and sends it
    to the detection provider for processing.

    Args:
        queue_id: ID of the queue item to process
    """
    logger.info(f"Starting detection frame processing for queue item: {queue_id}")

    try:
        import asyncio

        result = asyncio.run(_async_process_detection_frame(queue_id))
        logger.info(f"Frame processing completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Error during frame processing: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


async def _async_process_detection_frame(queue_id: str) -> dict:
    """Async implementation of frame processing."""
    async with AsyncSessionLocal() as session:
        queue_repo = DetectionProcessingQueueRepository(session)
        service = DetectionService(session)

        try:
            # Get queue item
            queue_item = await queue_repo.get_by_id(queue_id)
            if not queue_item:
                logger.warning(f"Queue item not found: {queue_id}")
                return {"success": False, "error": "Queue item not found"}

            # Mark as processing
            await queue_repo.update_status(queue_id, "processing")

            # Process frame
            result = await service.send_frame_for_detection(
                camera_id=queue_item.camera_id,
                frame_data=queue_item.frame_data,
                frame_number=queue_item.frame_number,
                frame_timestamp=queue_item.frame_timestamp,
            )

            # Mark as completed
            await queue_repo.mark_completed(
                queue_id=queue_id,
                detections_count=result["detection_count"],
                processing_time_ms=result["processing_time_ms"],
            )

            logger.info(f"Frame {queue_id} processed successfully: {result['detection_count']} detections")

            return {
                "success": True,
                "queue_id": queue_id,
                "detection_count": result["detection_count"],
                "processing_time_ms": result["processing_time_ms"],
            }

        except Exception as e:
            logger.error(f"Error processing frame {queue_id}: {e}")
            # Mark as failed (with retry logic)
            await queue_repo.mark_failed(queue_id=queue_id, error_message=str(e))
            raise


@app.task(
    name="worker.tasks.detection.send_frame_to_provider",
    bind=True,
    max_retries=2,
)
def send_frame_to_provider(self, camera_id: str, frame_data: bytes):
    """
    Send a single frame to the detection provider.

    This task is used for on-demand frame processing, not from the queue.

    Args:
        camera_id: Camera ID
        frame_data: Frame data as bytes
    """
    logger.info(f"Sending frame from camera {camera_id} to detection provider")

    try:
        import asyncio

        result = asyncio.run(_async_send_frame_to_provider(camera_id, frame_data))
        logger.info(f"Frame sent to provider: {result}")
        return result
    except Exception as e:
        logger.error(f"Error sending frame to provider: {e}")
        raise self.retry(exc=e, countdown=10 * (2 ** self.request.retries))


async def _async_send_frame_to_provider(camera_id: str, frame_data: bytes) -> dict:
    """Async implementation of sending frame to provider."""
    async with AsyncSessionLocal() as session:
        service = DetectionService(session)

        try:
            result = await service.send_frame_for_detection(
                camera_id=camera_id,
                frame_data=frame_data,
            )

            logger.info(f"Frame from camera {camera_id} processed: {result['detection_count']} detections")

            return {
                "success": True,
                "camera_id": camera_id,
                "detection_count": result["detection_count"],
                "processing_time_ms": result["processing_time_ms"],
            }

        except Exception as e:
            logger.error(f"Error processing frame from camera {camera_id}: {e}")
            raise


@app.task(
    name="worker.tasks.detection.test_detection_provider",
    bind=True,
)
def test_detection_provider(self, config_id: str = None):
    """
    Test detection provider connection.

    This task is typically run periodically to verify the provider is responding.

    Args:
        config_id: Provider configuration ID (optional, uses active if not provided)
    """
    logger.info(f"Testing detection provider connection: {config_id or 'active config'}")

    try:
        import asyncio

        result = asyncio.run(_async_test_detection_provider(config_id))
        logger.info(f"Provider test completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Error testing detection provider: {e}")
        raise


async def _async_test_detection_provider(config_id: str = None) -> dict:
    """Async implementation of provider testing."""
    async with AsyncSessionLocal() as session:
        service = DetectionService(session)

        try:
            result = await service.test_provider_connection(config_id=config_id)

            test_result = {
                "success": result.success,
                "provider_name": result.provider_name,
                "message": result.message,
                "response_time_ms": result.response_time_ms,
            }

            if result.success:
                logger.info(f"Provider test successful: {result.provider_name}")
            else:
                logger.warning(f"Provider test failed: {result.error}")
                test_result["error"] = result.error

            return test_result

        except Exception as e:
            logger.error(f"Error testing provider: {e}")
            raise


@app.task(
    name="worker.tasks.detection.cleanup_old_detections",
    bind=True,
)
def cleanup_old_detections(self, days: int = 30):
    """
    Clean up old detection records.

    This task runs periodically and removes detection records older than
    the specified number of days.

    Args:
        days: Number of days to keep (default 30 days)
    """
    logger.info(f"Starting cleanup of detection records older than {days} days")

    try:
        import asyncio

        result = asyncio.run(_async_cleanup_old_detections(days))
        logger.info(f"Detection cleanup completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Error during detection cleanup: {e}")
        raise


async def _async_cleanup_old_detections(days: int) -> dict:
    """Async implementation of detection cleanup."""
    async with AsyncSessionLocal() as session:
        service = DetectionService(session)

        # Clean up old detections
        deleted_detections = await service.cleanup_old_detections(days=days)

        # Clean up old event logs (90 days)
        deleted_events = await service.cleanup_old_events(days=90)

        # Clean up old queue records (7 days)
        deleted_queue = await service.cleanup_old_queue_records(days=7)

        logger.info(
            f"Cleanup completed: {deleted_detections} detections, "
            f"{deleted_events} events, {deleted_queue} queue items"
        )

        return {
            "deleted_detections": deleted_detections,
            "deleted_events": deleted_events,
            "deleted_queue_items": deleted_queue,
            "days_kept": days,
        }


@app.task(
    name="worker.tasks.detection.aggregate_detection_stats",
    bind=True,
)
def aggregate_detection_stats(self, camera_id: str = None):
    """
    Aggregate detection statistics.

    This task calculates and caches detection statistics for dashboards
    and monitoring systems.

    Args:
        camera_id: Camera ID (optional, for all cameras if not provided)
    """
    logger.info(f"Aggregating detection statistics for camera: {camera_id or 'all'}")

    try:
        import asyncio

        result = asyncio.run(_async_aggregate_detection_stats(camera_id))
        logger.info(f"Statistics aggregation completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Error during statistics aggregation: {e}")
        raise


async def _async_aggregate_detection_stats(camera_id: str = None) -> dict:
    """Async implementation of statistics aggregation."""
    async with AsyncSessionLocal() as session:
        service = DetectionService(session)

        try:
            # Get current statistics
            stats = await service.get_detection_statistics(camera_id=camera_id)

            # Get queue statistics
            queue_stats = await service.get_queue_stats()

            logger.info(
                f"Statistics for camera {camera_id or 'all'}: "
                f"{stats['detections_today']} today, "
                f"{stats['detections_this_hour']} this hour"
            )

            return {
                "success": True,
                "camera_id": camera_id,
                "statistics": stats,
                "queue_stats": queue_stats,
            }

        except Exception as e:
            logger.error(f"Error aggregating statistics: {e}")
            raise


@app.task(
    name="worker.tasks.detection.process_detection_queue",
    bind=True,
)
def process_detection_queue(self, limit: int = 10):
    """
    Process pending items from the detection queue.

    This task is typically run periodically to process accumulated frames.

    Args:
        limit: Maximum number of items to process in this run
    """
    logger.info(f"Processing detection queue (limit: {limit})")

    try:
        import asyncio

        result = asyncio.run(_async_process_detection_queue(limit))
        logger.info(f"Queue processing completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Error processing detection queue: {e}")
        raise


async def _async_process_detection_queue(limit: int) -> dict:
    """Async implementation of queue processing."""
    async with AsyncSessionLocal() as session:
        queue_repo = DetectionProcessingQueueRepository(session)
        service = DetectionService(session)

        try:
            # Get pending items
            pending_items = await queue_repo.get_pending(limit=limit)

            if not pending_items:
                logger.info("No pending detection queue items to process")
                return {
                    "success": True,
                    "processed_count": 0,
                    "message": "No pending items",
                }

            logger.info(f"Found {len(pending_items)} pending items to process")

            processed_count = 0
            failed_count = 0

            # Process each item
            for queue_item in pending_items:
                try:
                    # Mark as processing
                    await queue_repo.update_status(queue_item.id, "processing")

                    # Process frame
                    result = await service.send_frame_for_detection(
                        camera_id=queue_item.camera_id,
                        frame_data=queue_item.frame_data,
                        frame_number=queue_item.frame_number,
                        frame_timestamp=queue_item.frame_timestamp,
                    )

                    # Mark as completed
                    await queue_repo.mark_completed(
                        queue_id=queue_item.id,
                        detections_count=result["detection_count"],
                        processing_time_ms=result["processing_time_ms"],
                    )

                    processed_count += 1

                except Exception as e:
                    logger.error(f"Error processing queue item {queue_item.id}: {e}")
                    await queue_repo.mark_failed(
                        queue_id=queue_item.id,
                        error_message=str(e),
                    )
                    failed_count += 1

            logger.info(f"Queue processing completed: {processed_count} processed, {failed_count} failed")

            return {
                "success": True,
                "processed_count": processed_count,
                "failed_count": failed_count,
                "total_processed": processed_count + failed_count,
            }

        except Exception as e:
            logger.error(f"Error in queue processing: {e}")
            raise
