"""FFmpeg service for video processing and snapshot capture."""

import asyncio
import logging
import subprocess
from typing import Optional
from uuid import uuid4

from app.core.config import settings
from app.core.errors import ValidationError

logger = logging.getLogger(__name__)


class FFmpegService:
    """Service for FFmpeg video operations."""

    def __init__(self):
        """Initialize FFmpeg service."""
        self.ffmpeg_path = settings.FFMPEG_PATH or "ffmpeg"
        self.timeout = settings.FFMPEG_TIMEOUT
        self._verify_ffmpeg()

    def _verify_ffmpeg(self) -> None:
        """Verify FFmpeg is installed."""
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                timeout=5,
            )
            if result.returncode == 0:
                logger.info("FFmpeg is available")
            else:
                logger.warning("FFmpeg verification failed")
        except FileNotFoundError:
            logger.warning(f"FFmpeg not found at {self.ffmpeg_path}")
        except Exception as e:
            logger.warning(f"Failed to verify FFmpeg: {e}")

    async def capture_snapshot(
        self,
        rtsp_url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ) -> Optional[bytes]:
        """
        Capture a single frame from RTSP stream.

        Args:
            rtsp_url: RTSP stream URL
            username: Optional username
            password: Optional password
            timeout_seconds: Timeout for capture

        Returns:
            JPEG image bytes, or None if failed
        """
        timeout = timeout_seconds or self.timeout

        # Prepare authentication if needed
        if username and password:
            # Parse RTSP URL and add credentials
            rtsp_url = self._add_credentials_to_url(rtsp_url, username, password)

        try:
            # FFmpeg command to capture single frame
            cmd = [
                self.ffmpeg_path,
                "-rtsp_transport", "tcp",
                "-i", rtsp_url,
                "-vframes", "1",
                "-q:v", "2",  # Quality (1=best, 31=worst)
                "-f", "image2",
                "-",  # Output to stdout
            ]

            logger.debug(f"Executing FFmpeg command to capture snapshot")

            # Run FFmpeg command
            result = await asyncio.wait_for(
                self._run_ffmpeg(cmd),
                timeout=timeout,
            )

            if result and len(result) > 0:
                logger.info(f"Snapshot captured successfully")
                return result
            else:
                logger.warning("No data returned from FFmpeg")
                return None

        except asyncio.TimeoutError:
            logger.error(f"Snapshot capture timed out after {timeout}s")
            return None
        except Exception as e:
            logger.error(f"Failed to capture snapshot: {e}")
            return None

    async def test_rtsp_connection(
        self,
        rtsp_url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ) -> dict:
        """
        Test RTSP stream connection.

        Args:
            rtsp_url: RTSP stream URL
            username: Optional username
            password: Optional password
            timeout_seconds: Timeout for test

        Returns:
            Test result dictionary
        """
        timeout = timeout_seconds or self.timeout

        if username and password:
            rtsp_url = self._add_credentials_to_url(rtsp_url, username, password)

        try:
            # FFmpeg command to test connection and probe stream
            cmd = [
                self.ffmpeg_path,
                "-rtsp_transport", "tcp",
                "-i", rtsp_url,
                "-t", "1",  # Read for 1 second only
                "-f", "null",
                "-",
            ]

            import time
            start_time = time.time()

            result = await asyncio.wait_for(
                self._run_ffmpeg_with_stderr(cmd),
                timeout=timeout,
            )

            elapsed_time = time.time() - start_time

            if result and result.get("success"):
                info = result.get("info", {})
                return {
                    "success": True,
                    "message": "Connection successful",
                    "latency_ms": int(elapsed_time * 1000),
                    "resolution": info.get("resolution"),
                    "fps": info.get("fps"),
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to connect",
                    "error": result.get("error") if result else "Unknown error",
                }

        except asyncio.TimeoutError:
            return {
                "success": False,
                "message": f"Connection timed out after {timeout}s",
                "error": "Timeout",
            }
        except Exception as e:
            return {
                "success": False,
                "message": "Connection test failed",
                "error": str(e),
            }

    async def convert_video(
        self,
        input_path: str,
        output_path: str,
        codec: str = "h264",
        timeout_seconds: Optional[int] = None,
    ) -> bool:
        """
        Convert video to specified codec.

        Args:
            input_path: Input file path
            output_path: Output file path
            codec: Target codec (h264, h265, vp9, etc.)
            timeout_seconds: Timeout for conversion

        Returns:
            True if successful
        """
        timeout = timeout_seconds or self.timeout * 2

        try:
            # FFmpeg command for conversion
            if codec == "h265":
                preset = "veryfast"
                crf = "28"
                encoder = "libx265"
            elif codec == "vp9":
                encoder = "libvpx-vp9"
                preset = "6"
                crf = "30"
            else:  # h264
                encoder = "libx264"
                preset = "veryfast"
                crf = "23"

            cmd = [
                self.ffmpeg_path,
                "-i", input_path,
                "-c:v", encoder,
                "-preset", preset,
                "-crf", crf,
                "-c:a", "aac",
                "-b:a", "128k",
                output_path,
                "-y",  # Overwrite output
            ]

            result = await asyncio.wait_for(
                self._run_ffmpeg(cmd),
                timeout=timeout,
            )

            return True if result else False

        except asyncio.TimeoutError:
            logger.error(f"Video conversion timed out")
            return False
        except Exception as e:
            logger.error(f"Failed to convert video: {e}")
            return False

    def _add_credentials_to_url(self, rtsp_url: str, username: str, password: str) -> str:
        """
        Add credentials to RTSP URL.

        Args:
            rtsp_url: RTSP URL
            username: Username
            password: Password

        Returns:
            RTSP URL with credentials
        """
        # Parse URL and insert credentials
        if "://" in rtsp_url:
            protocol, rest = rtsp_url.split("://", 1)
            return f"{protocol}://{username}:{password}@{rest}"
        return rtsp_url

    async def _run_ffmpeg(self, cmd: list) -> Optional[bytes]:
        """
        Run FFmpeg command and return stdout.

        Args:
            cmd: Command list

        Returns:
            Stdout bytes, or None if failed
        """
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode(errors="ignore") if stderr else "Unknown error"
                logger.debug(f"FFmpeg error: {error_msg}")
                return None

            return stdout

        except Exception as e:
            logger.error(f"Failed to run FFmpeg: {e}")
            return None

    async def _run_ffmpeg_with_stderr(self, cmd: list) -> dict:
        """
        Run FFmpeg and parse stderr for info.

        Args:
            cmd: Command list

        Returns:
            Result dictionary with success and info
        """
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()
            stderr_text = stderr.decode(errors="ignore") if stderr else ""

            # Parse FFmpeg output for stream information
            info = self._parse_ffmpeg_output(stderr_text)

            return {
                "success": process.returncode == 0,
                "info": info,
            }

        except Exception as e:
            logger.error(f"Failed to run FFmpeg with stderr parsing: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def _parse_ffmpeg_output(self, output: str) -> dict:
        """
        Parse FFmpeg output to extract stream info.

        Args:
            output: FFmpeg stderr output

        Returns:
            Parsed information
        """
        info = {}

        # Try to find resolution
        import re

        # Look for video stream resolution
        resolution_match = re.search(r'(\d{3,4}x\d{3,4})', output)
        if resolution_match:
            info["resolution"] = resolution_match.group(1)

        # Look for FPS information
        fps_match = re.search(r'(\d+(?:\.\d+)?)\s*fps', output)
        if fps_match:
            try:
                info["fps"] = int(float(fps_match.group(1)))
            except (ValueError, AttributeError):
                pass

        return info
