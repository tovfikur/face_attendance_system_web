"""Detection provider service for communication with external detection systems."""

import base64
import io
import json
import logging
from typing import Optional
from uuid import uuid4

import httpx
from PIL import Image

from app.core.config import settings
from app.core.errors import ValidationError
from app.schemas.detection import (
    DetectionResponse,
    BoundingBox,
    TestDetectionProviderResponse,
)

logger = logging.getLogger(__name__)


class DetectionProviderService:
    """Service for communicating with external detection providers."""

    def __init__(self):
        """Initialize detection provider service."""
        self.timeout = settings.DETECTION_PROVIDER_TIMEOUT or 30
        self.max_retries = settings.DETECTION_PROVIDER_MAX_RETRIES or 3

    async def send_frame_to_provider(
        self,
        provider_endpoint: str,
        frame_data: bytes,
        api_key: Optional[str] = None,
        timeout: Optional[int] = None,
        **kwargs,
    ) -> dict:
        """
        Send frame to detection provider for processing.

        Args:
            provider_endpoint: Provider API endpoint URL
            frame_data: Frame as bytes (PNG, JPG, etc.)
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
            **kwargs: Additional parameters (confidence_threshold, max_faces, etc.)

        Returns:
            Detection results from provider
        """
        timeout = timeout or self.timeout

        try:
            # Prepare headers
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            # Prepare request body
            frame_b64 = base64.b64encode(frame_data).decode()
            payload = {
                "frame": frame_b64,
                "format": "base64",
                **kwargs,
            }

            # Send request
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    provider_endpoint,
                    json=payload,
                    headers=headers,
                )

                if response.status_code != 200:
                    logger.error(f"Provider returned status {response.status_code}: {response.text}")
                    raise ValidationError(f"Provider error: {response.status_code}")

                result = response.json()
                return result

        except httpx.TimeoutException:
            logger.error(f"Detection provider request timed out after {timeout}s")
            raise ValidationError(f"Provider request timed out")
        except httpx.RequestError as e:
            logger.error(f"Detection provider request failed: {e}")
            raise ValidationError(f"Provider connection error: {str(e)}")
        except Exception as e:
            logger.error(f"Error sending frame to detection provider: {e}")
            raise ValidationError(f"Failed to process frame: {str(e)}")

    async def test_provider_connection(
        self,
        provider_endpoint: str,
        api_key: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> TestDetectionProviderResponse:
        """
        Test connection to detection provider.

        Args:
            provider_endpoint: Provider API endpoint
            api_key: Optional API key
            timeout: Request timeout in seconds

        Returns:
            Test result
        """
        timeout = timeout or 10

        try:
            # Create a simple test frame (1x1 white pixel)
            test_frame = self._create_test_frame()

            # Send to provider
            result = await self.send_frame_to_provider(
                provider_endpoint,
                test_frame,
                api_key=api_key,
                timeout=timeout,
            )

            return TestDetectionProviderResponse(
                success=True,
                provider_name="Unknown",  # Could be extracted from config
                message="Connection successful",
                response_time_ms=int((result.get("processing_time_ms", 0))),
                error=None,
            )

        except ValidationError as e:
            return TestDetectionProviderResponse(
                success=False,
                provider_name="Unknown",
                message="Connection failed",
                error=str(e),
            )
        except Exception as e:
            logger.error(f"Provider test failed: {e}")
            return TestDetectionProviderResponse(
                success=False,
                provider_name="Unknown",
                message="Connection failed",
                error=str(e),
            )

    def parse_provider_response(
        self,
        camera_id: str,
        provider_response: dict,
    ) -> list[DetectionResponse]:
        """
        Parse detection provider response and convert to our schema.

        Args:
            camera_id: Camera ID
            provider_response: Raw response from provider

        Returns:
            List of DetectionResponse objects
        """
        detections = []

        try:
            # Extract detections from provider response
            # This assumes a standard format, but will need to be customized
            # based on the actual provider's response format

            detections_data = provider_response.get("detections", [])

            for detection_data in detections_data:
                try:
                    # Extract bounding box
                    bbox_data = detection_data.get("bbox", {})
                    bbox = BoundingBox(
                        x=float(bbox_data.get("x", 0)),
                        y=float(bbox_data.get("y", 0)),
                        width=float(bbox_data.get("width", 0)),
                        height=float(bbox_data.get("height", 0)),
                    )

                    # Create detection response
                    detection = DetectionResponse(
                        id=str(uuid4()),
                        camera_id=camera_id,
                        detection_type=detection_data.get("type", "person"),
                        confidence=float(detection_data.get("confidence", 0)),
                        bbox=bbox,
                        person_name=detection_data.get("person_name"),
                        person_id=detection_data.get("person_id"),
                        face_encoding=detection_data.get("face_encoding"),
                        is_processed=False,
                        processing_status="completed",
                        frame_number=provider_response.get("frame_number"),
                        frame_timestamp=provider_response.get("frame_timestamp"),
                        createdAt=__import__("datetime").datetime.utcnow(),
                        updatedAt=__import__("datetime").datetime.utcnow(),
                    )

                    detections.append(detection)

                except Exception as e:
                    logger.warning(f"Failed to parse detection: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error parsing provider response: {e}")

        return detections

    async def send_batch_frames(
        self,
        provider_endpoint: str,
        frames: list[bytes],
        api_key: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> dict:
        """
        Send multiple frames for batch processing.

        Args:
            provider_endpoint: Provider API endpoint
            frames: List of frame bytes
            api_key: Optional API key
            timeout: Request timeout

        Returns:
            Batch processing result
        """
        timeout = timeout or self.timeout

        try:
            # Encode frames to base64
            encoded_frames = [base64.b64encode(frame).decode() for frame in frames]

            # Prepare headers
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            # Prepare batch request
            payload = {
                "frames": encoded_frames,
                "format": "base64",
                "batch": True,
            }

            # Send request
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    provider_endpoint,
                    json=payload,
                    headers=headers,
                )

                if response.status_code != 200:
                    raise ValidationError(f"Provider error: {response.status_code}")

                return response.json()

        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            raise ValidationError(f"Batch processing failed: {str(e)}")

    def _create_test_frame(self, width: int = 100, height: int = 100) -> bytes:
        """
        Create a simple test frame.

        Args:
            width: Frame width
            height: Frame height

        Returns:
            Frame as bytes (JPEG)
        """
        try:
            # Create a simple white image
            image = Image.new("RGB", (width, height), color="white")

            # Convert to JPEG bytes
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG")
            return buffer.getvalue()

        except Exception as e:
            logger.error(f"Failed to create test frame: {e}")
            # Return a minimal valid JPEG as fallback
            return b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9"

    async def get_provider_capabilities(
        self,
        provider_endpoint: str,
        api_key: Optional[str] = None,
    ) -> dict:
        """
        Get capabilities/info from detection provider.

        Args:
            provider_endpoint: Provider API endpoint
            api_key: Optional API key

        Returns:
            Provider capabilities
        """
        try:
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{provider_endpoint}/info",
                    headers=headers,
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Failed to get provider info: {response.status_code}")
                    return {}

        except Exception as e:
            logger.error(f"Error getting provider capabilities: {e}")
            return {}
