"""Face recognition service for face encoding and matching."""

import io
import logging
from typing import Optional

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# Import face_recognition library - handles face detection and encoding
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    logger.warning("face_recognition library not available. Install with: pip install face_recognition")


class FaceRecognitionService:
    """Service for face recognition and matching."""

    # Face matching thresholds
    DEFAULT_TOLERANCE = 0.6  # Distance threshold for matching (0.0-1.0)
    GOOD_MATCH_THRESHOLD = 0.5  # Confidence > 0.5 considered good match
    EXCELLENT_MATCH_THRESHOLD = 0.4  # Confidence > 0.4 considered excellent

    def __init__(self, tolerance: float = DEFAULT_TOLERANCE):
        """Initialize face recognition service."""
        self.tolerance = tolerance
        self.model = "hog"  # "hog" for CPU, "cnn" for GPU

        if not FACE_RECOGNITION_AVAILABLE:
            logger.warning("Face recognition service initialized without library support")

    def extract_face_encoding(
        self,
        image_data: bytes,
        include_metadata: bool = False,
    ) -> Optional[dict]:
        """
        Extract face encoding from image.

        Args:
            image_data: Image as bytes (PNG, JPG, etc.)
            include_metadata: Include face location and quality metrics

        Returns:
            Dictionary with encoding and metadata, or None if no face detected
        """
        if not FACE_RECOGNITION_AVAILABLE:
            logger.error("Face recognition library not available")
            return None

        try:
            # Load image
            image = Image.open(io.BytesIO(image_data))
            image_array = np.array(image)

            # Detect faces
            face_locations = face_recognition.face_locations(image_array, model=self.model)

            if not face_locations:
                logger.warning("No faces detected in image")
                return None

            if len(face_locations) > 1:
                logger.warning(f"Multiple faces detected ({len(face_locations)}), using first")

            # Extract encoding from first face
            encodings = face_recognition.face_encodings(image_array, face_locations)

            if not encodings:
                logger.warning("Failed to extract encoding from detected face")
                return None

            encoding = encodings[0]

            result = {
                "encoding": encoding.tobytes(),  # Store as binary for DB
                "encoding_list": encoding.tolist(),  # For computation
                "encoding_shape": encoding.shape,
                "face_detected": True,
            }

            if include_metadata:
                face_location = face_locations[0]
                top, right, bottom, left = face_location

                # Calculate face size and position
                face_width = right - left
                face_height = bottom - top
                image_width, image_height = image.size

                result.update(
                    {
                        "face_location": {
                            "top": top,
                            "right": right,
                            "bottom": bottom,
                            "left": left,
                        },
                        "face_size": {
                            "width": face_width,
                            "height": face_height,
                        },
                        "image_size": {
                            "width": image_width,
                            "height": image_height,
                        },
                        "face_area_percentage": (face_width * face_height) / (image_width * image_height),
                        "number_of_faces": len(face_locations),
                    }
                )

            logger.info("Face encoding extracted successfully")
            return result

        except Exception as e:
            logger.error(f"Error extracting face encoding: {e}")
            return None

    def compare_face_encodings(
        self,
        encoding1: bytes,
        encoding2: bytes,
    ) -> float:
        """
        Compare two face encodings.

        Args:
            encoding1: First face encoding (bytes from DB)
            encoding2: Second face encoding (bytes from DB)

        Returns:
            Distance score (0.0 = identical, 1.0 = different)
        """
        if not FACE_RECOGNITION_AVAILABLE:
            logger.error("Face recognition library not available")
            return 1.0

        try:
            # Convert bytes back to numpy arrays
            enc1 = np.frombuffer(encoding1, dtype=np.float64).reshape((128,))
            enc2 = np.frombuffer(encoding2, dtype=np.float64).reshape((128,))

            # Calculate Euclidean distance
            distance = np.linalg.norm(enc1 - enc2)

            return float(distance)

        except Exception as e:
            logger.error(f"Error comparing face encodings: {e}")
            return 1.0

    def compare_face_encodings_list(
        self,
        encoding1: list,
        encoding2: list,
    ) -> float:
        """
        Compare face encodings provided as lists.

        Args:
            encoding1: First face encoding (list)
            encoding2: Second face encoding (list)

        Returns:
            Distance score (0.0 = identical, 1.0 = different)
        """
        try:
            enc1 = np.array(encoding1)
            enc2 = np.array(encoding2)
            distance = np.linalg.norm(enc1 - enc2)
            return float(distance)
        except Exception as e:
            logger.error(f"Error comparing encodings: {e}")
            return 1.0

    def match_face(
        self,
        face_encoding: bytes,
        known_encodings: list[bytes],
        tolerance: Optional[float] = None,
    ) -> dict:
        """
        Match a face against a list of known encodings.

        Args:
            face_encoding: Face encoding to match (bytes)
            known_encodings: List of known face encodings (bytes)
            tolerance: Match tolerance (default: self.tolerance)

        Returns:
            Dictionary with match results:
            {
                "is_match": bool,
                "best_match_index": int or None,
                "best_match_distance": float,
                "all_distances": list[float],
                "confidence": float (0.0-1.0, inverted distance)
            }
        """
        if not known_encodings:
            return {
                "is_match": False,
                "best_match_index": None,
                "best_match_distance": 1.0,
                "all_distances": [],
                "confidence": 0.0,
            }

        tolerance = tolerance or self.tolerance

        try:
            # Compare against all known encodings
            distances = []
            for known_encoding in known_encodings:
                distance = self.compare_face_encodings(face_encoding, known_encoding)
                distances.append(distance)

            # Find best match
            best_match_index = np.argmin(distances)
            best_match_distance = distances[best_match_index]

            # Check if within tolerance
            is_match = best_match_distance <= tolerance

            # Calculate confidence (inverted distance: 1.0 - distance)
            confidence = max(0.0, 1.0 - best_match_distance)

            return {
                "is_match": is_match,
                "best_match_index": best_match_index if is_match else None,
                "best_match_distance": best_match_distance,
                "all_distances": distances,
                "confidence": confidence,
            }

        except Exception as e:
            logger.error(f"Error matching face: {e}")
            return {
                "is_match": False,
                "best_match_index": None,
                "best_match_distance": 1.0,
                "all_distances": [],
                "confidence": 0.0,
            }

    def match_face_list(
        self,
        face_encoding_list: list,
        known_encodings_list: list[list],
        tolerance: Optional[float] = None,
    ) -> dict:
        """
        Match a face (as list) against known encodings (as lists).

        Args:
            face_encoding_list: Face encoding (list)
            known_encodings_list: List of known encodings (list of lists)
            tolerance: Match tolerance

        Returns:
            Match results dictionary
        """
        if not known_encodings_list:
            return {
                "is_match": False,
                "best_match_index": None,
                "best_match_distance": 1.0,
                "all_distances": [],
                "confidence": 0.0,
            }

        tolerance = tolerance or self.tolerance

        try:
            face_enc = np.array(face_encoding_list)

            # Calculate distances
            distances = []
            for known_enc in known_encodings_list:
                known_enc_arr = np.array(known_enc)
                distance = np.linalg.norm(face_enc - known_enc_arr)
                distances.append(float(distance))

            # Find best match
            best_match_index = np.argmin(distances)
            best_match_distance = distances[best_match_index]

            # Check if within tolerance
            is_match = best_match_distance <= tolerance

            # Calculate confidence
            confidence = max(0.0, 1.0 - best_match_distance)

            return {
                "is_match": is_match,
                "best_match_index": best_match_index if is_match else None,
                "best_match_distance": best_match_distance,
                "all_distances": distances,
                "confidence": confidence,
            }

        except Exception as e:
            logger.error(f"Error matching face (list): {e}")
            return {
                "is_match": False,
                "best_match_index": None,
                "best_match_distance": 1.0,
                "all_distances": [],
                "confidence": 0.0,
            }

    def detect_faces(self, image_data: bytes) -> Optional[dict]:
        """
        Detect faces in an image without encoding.

        Args:
            image_data: Image as bytes

        Returns:
            Dictionary with face detection results
        """
        if not FACE_RECOGNITION_AVAILABLE:
            logger.error("Face recognition library not available")
            return None

        try:
            image = Image.open(io.BytesIO(image_data))
            image_array = np.array(image)

            face_locations = face_recognition.face_locations(image_array, model=self.model)

            if not face_locations:
                return {
                    "faces_detected": 0,
                    "face_locations": [],
                }

            face_data = []
            for top, right, bottom, left in face_locations:
                face_data.append(
                    {
                        "top": int(top),
                        "right": int(right),
                        "bottom": int(bottom),
                        "left": int(left),
                        "width": int(right - left),
                        "height": int(bottom - top),
                    }
                )

            return {
                "faces_detected": len(face_locations),
                "face_locations": face_data,
            }

        except Exception as e:
            logger.error(f"Error detecting faces: {e}")
            return None

    def get_confidence_level(self, distance: float) -> str:
        """
        Get confidence level description from distance.

        Args:
            distance: Face distance (0.0-1.0)

        Returns:
            Confidence level description
        """
        if distance <= self.EXCELLENT_MATCH_THRESHOLD:
            return "excellent"
        elif distance <= self.GOOD_MATCH_THRESHOLD:
            return "good"
        elif distance <= self.tolerance:
            return "acceptable"
        else:
            return "poor"

    def calculate_average_encoding(self, encodings: list[bytes]) -> bytes:
        """
        Calculate average encoding from multiple encodings.

        Useful for improving match accuracy by averaging multiple face samples.

        Args:
            encodings: List of face encodings (bytes)

        Returns:
            Average encoding as bytes
        """
        if not encodings:
            raise ValueError("No encodings provided")

        try:
            enc_arrays = []
            for enc in encodings:
                enc_array = np.frombuffer(enc, dtype=np.float64).reshape((128,))
                enc_arrays.append(enc_array)

            average = np.mean(enc_arrays, axis=0)
            return average.tobytes()

        except Exception as e:
            logger.error(f"Error calculating average encoding: {e}")
            raise
