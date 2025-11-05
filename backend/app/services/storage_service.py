"""MinIO S3 storage service for file management."""

import logging
from datetime import timedelta
from io import BytesIO
from typing import Optional

from minio import Minio
from minio.error import S3Error

from app.core.config import settings
from app.core.errors import ValidationError

logger = logging.getLogger(__name__)


class StorageService:
    """Service for MinIO S3 storage operations."""

    def __init__(self):
        """Initialize MinIO client."""
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
            region=settings.MINIO_REGION,
        )
        self.bucket = settings.MINIO_BUCKET
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """Ensure bucket exists, create if not."""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                logger.info(f"Created MinIO bucket: {self.bucket}")
        except S3Error as e:
            logger.error(f"Failed to create MinIO bucket: {e}")

    async def upload_file(
        self,
        file_path: str,
        file_data: bytes,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        Upload file to MinIO.

        Args:
            file_path: Path in MinIO (e.g., "snapshots/camera_id/file.jpg")
            file_data: File content as bytes
            content_type: MIME type
            metadata: Optional metadata dictionary

        Returns:
            Upload result with file info
        """
        try:
            file_size = len(file_data)

            # Validate file size (max 100MB)
            if file_size > 100 * 1024 * 1024:
                raise ValidationError("File size exceeds maximum limit of 100MB")

            # Prepare metadata
            if metadata is None:
                metadata = {}

            # Upload file
            result = self.client.put_object(
                bucket_name=self.bucket,
                object_name=file_path,
                data=BytesIO(file_data),
                length=file_size,
                content_type=content_type,
                metadata=metadata,
            )

            logger.info(f"Uploaded file to MinIO: {file_path}")

            return {
                "success": True,
                "path": file_path,
                "size": file_size,
                "etag": result.etag,
                "version_id": result.version_id,
            }
        except S3Error as e:
            logger.error(f"Failed to upload file to MinIO: {e}")
            raise ValidationError(f"Failed to upload file: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error uploading file: {e}")
            raise

    async def download_file(self, file_path: str) -> bytes:
        """
        Download file from MinIO.

        Args:
            file_path: Path in MinIO

        Returns:
            File content as bytes
        """
        try:
            response = self.client.get_object(self.bucket, file_path)
            file_data = response.read()
            response.close()
            return file_data
        except S3Error as e:
            logger.error(f"Failed to download file from MinIO: {e}")
            raise ValidationError(f"Failed to download file: {str(e)}")

    async def generate_signed_url(
        self,
        file_path: str,
        expires_in_hours: int = 24,
    ) -> str:
        """
        Generate signed URL for file access.

        Args:
            file_path: Path in MinIO
            expires_in_hours: URL expiration time in hours

        Returns:
            Signed URL
        """
        try:
            expires = timedelta(hours=expires_in_hours)
            url = self.client.get_presigned_download_url(
                bucket_name=self.bucket,
                object_name=file_path,
                expires=expires,
            )
            return url
        except S3Error as e:
            logger.error(f"Failed to generate signed URL: {e}")
            raise ValidationError(f"Failed to generate signed URL: {str(e)}")

    async def delete_file(self, file_path: str) -> bool:
        """
        Delete file from MinIO.

        Args:
            file_path: Path in MinIO

        Returns:
            True if deleted, False if not found
        """
        try:
            self.client.remove_object(self.bucket, file_path)
            logger.info(f"Deleted file from MinIO: {file_path}")
            return True
        except S3Error as e:
            if "does not exist" in str(e):
                return False
            logger.error(f"Failed to delete file from MinIO: {e}")
            raise ValidationError(f"Failed to delete file: {str(e)}")

    async def delete_directory(self, directory_path: str) -> int:
        """
        Delete all files in a directory.

        Args:
            directory_path: Directory path in MinIO (e.g., "snapshots/camera_id/")

        Returns:
            Number of files deleted
        """
        try:
            objects = self.client.list_objects(self.bucket, prefix=directory_path)
            deleted_count = 0

            for obj in objects:
                self.client.remove_object(self.bucket, obj.object_name)
                deleted_count += 1

            if deleted_count > 0:
                logger.info(f"Deleted {deleted_count} files from directory: {directory_path}")

            return deleted_count
        except S3Error as e:
            logger.error(f"Failed to delete directory from MinIO: {e}")
            raise ValidationError(f"Failed to delete directory: {str(e)}")

    async def file_exists(self, file_path: str) -> bool:
        """
        Check if file exists in MinIO.

        Args:
            file_path: Path in MinIO

        Returns:
            True if exists, False otherwise
        """
        try:
            self.client.stat_object(self.bucket, file_path)
            return True
        except S3Error as e:
            if "does not exist" in str(e):
                return False
            logger.error(f"Failed to check file existence: {e}")
            return False

    async def get_file_size(self, file_path: str) -> Optional[int]:
        """
        Get file size from MinIO.

        Args:
            file_path: Path in MinIO

        Returns:
            File size in bytes, or None if not found
        """
        try:
            stat = self.client.stat_object(self.bucket, file_path)
            return stat.size
        except S3Error as e:
            if "does not exist" in str(e):
                return None
            logger.error(f"Failed to get file size: {e}")
            return None

    async def list_files(self, directory_path: str) -> list[dict]:
        """
        List files in a directory.

        Args:
            directory_path: Directory path in MinIO

        Returns:
            List of file info dictionaries
        """
        try:
            objects = self.client.list_objects(self.bucket, prefix=directory_path)
            files = []

            for obj in objects:
                files.append({
                    "name": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified,
                    "etag": obj.etag,
                })

            return files
        except S3Error as e:
            logger.error(f"Failed to list files: {e}")
            raise ValidationError(f"Failed to list files: {str(e)}")

    async def copy_file(self, source_path: str, dest_path: str) -> bool:
        """
        Copy file within MinIO.

        Args:
            source_path: Source file path
            dest_path: Destination file path

        Returns:
            True if successful
        """
        try:
            self.client.copy_object(
                bucket_name=self.bucket,
                object_name=dest_path,
                source=f"/{self.bucket}/{source_path}",
            )
            logger.info(f"Copied file from {source_path} to {dest_path}")
            return True
        except S3Error as e:
            logger.error(f"Failed to copy file: {e}")
            raise ValidationError(f"Failed to copy file: {str(e)}")

    async def get_bucket_stats(self) -> dict:
        """
        Get bucket statistics.

        Returns:
            Bucket statistics
        """
        try:
            objects = self.client.list_objects(self.bucket)
            total_files = 0
            total_size = 0

            for obj in objects:
                total_files += 1
                total_size += obj.size

            return {
                "bucket": self.bucket,
                "total_files": total_files,
                "total_size": total_size,
                "total_size_mb": total_size / (1024 * 1024),
            }
        except S3Error as e:
            logger.error(f"Failed to get bucket stats: {e}")
            return {
                "bucket": self.bucket,
                "error": str(e),
            }
