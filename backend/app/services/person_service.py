"""Person service for person management and face enrollment."""

import base64
import logging
from typing import Optional
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationError
from app.models.person import Person, PersonFaceEncoding, PersonImage
from app.repositories.person import (
    PersonFaceEncodingRepository,
    PersonImageRepository,
    PersonRepository,
)
from app.schemas.person import (
    PersonCreate,
    PersonEnrollmentResponse,
    PersonSearchByFaceResponse,
    PersonUpdate,
)
from app.services.face_recognition_service import FaceRecognitionService

logger = logging.getLogger(__name__)


class PersonService:
    """Service for person management operations."""

    def __init__(self, db: AsyncSession):
        """Initialize person service."""
        self.db = db
        self.repo = PersonRepository(db)
        self.encoding_repo = PersonFaceEncodingRepository(db)
        self.image_repo = PersonImageRepository(db)
        self.face_service = FaceRecognitionService()

    # =========================================================================
    # Person CRUD Operations
    # =========================================================================

    async def create_person(self, request: PersonCreate) -> Person:
        """Create a new person."""
        # Check for duplicate email
        if request.email:
            existing = await self.repo.get_by_email(request.email)
            if existing:
                raise ValidationError(f"Person with email {request.email} already exists")

        # Check for duplicate ID number
        if request.id_number:
            existing = await self.repo.get_by_id_number(request.id_number)
            if existing:
                raise ValidationError(f"Person with ID number {request.id_number} already exists")

        person_id = str(uuid4())
        person = await self.repo.create(
            person_id=person_id,
            first_name=request.first_name,
            last_name=request.last_name,
            email=request.email,
            phone=request.phone,
            person_type=request.person_type,
            id_number=request.id_number,
            id_type=request.id_type,
            department=request.department,
            organization=request.organization,
            status=request.status,
        )

        logger.info(f"Created person: {person_id} - {person.first_name} {person.last_name}")
        return person

    async def get_person(self, person_id: str) -> Person:
        """Get person by ID."""
        person = await self.repo.get_by_id(person_id)
        if not person:
            raise NotFoundError(f"Person {person_id} not found")
        return person

    async def get_person_by_email(self, email: str) -> Person:
        """Get person by email."""
        person = await self.repo.get_by_email(email)
        if not person:
            raise NotFoundError(f"Person with email {email} not found")
        return person

    async def update_person(self, person_id: str, request: PersonUpdate) -> Person:
        """Update person information."""
        person = await self.get_person(person_id)

        # Check for duplicate email if email is being changed
        if request.email and request.email != person.email:
            existing = await self.repo.get_by_email(request.email)
            if existing:
                raise ValidationError(f"Person with email {request.email} already exists")

        # Check for duplicate ID number if ID is being changed
        if request.id_number and request.id_number != person.id_number:
            existing = await self.repo.get_by_id_number(request.id_number)
            if existing:
                raise ValidationError(f"Person with ID number {request.id_number} already exists")

        updated = await self.repo.update(person_id, **request.dict(exclude_unset=True))
        if not updated:
            raise NotFoundError(f"Person {person_id} not found")

        logger.info(f"Updated person: {person_id}")
        return updated

    async def delete_person(self, person_id: str) -> bool:
        """Delete person."""
        await self.get_person(person_id)  # Verify exists
        result = await self.repo.delete(person_id)
        if result:
            logger.info(f"Deleted person: {person_id}")
        return result

    async def list_persons(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        person_type: Optional[str] = None,
        department: Optional[str] = None,
    ) -> list[Person]:
        """List persons with optional filtering."""
        persons = await self.repo.get_all(skip=skip, limit=limit)

        # Filter by status
        if status:
            persons = [p for p in persons if p.status == status]

        # Filter by person type
        if person_type:
            persons = [p for p in persons if p.person_type == person_type]

        # Filter by department
        if department:
            persons = [p for p in persons if p.department == department]

        return persons

    async def search_persons(self, query: str) -> list[Person]:
        """Search persons by name, email, or ID number."""
        return await self.repo.search(query)

    # =========================================================================
    # Face Enrollment Methods
    # =========================================================================

    async def enroll_face(
        self,
        person_id: str,
        frame_data: str,
        is_primary: bool = False,
        quality_score: Optional[float] = None,
    ) -> PersonEnrollmentResponse:
        """
        Enroll a face for a person.

        Args:
            person_id: Person ID
            frame_data: Base64 encoded face image
            is_primary: Set as primary image
            quality_score: Image quality score (0.0-1.0)

        Returns:
            Enrollment response
        """
        try:
            person = await self.get_person(person_id)

            # Decode frame
            frame_bytes = base64.b64decode(frame_data)

            # Extract face encoding
            encoding_result = self.face_service.extract_face_encoding(
                frame_bytes,
                include_metadata=True
            )

            if not encoding_result or not encoding_result.get("face_detected"):
                return PersonEnrollmentResponse(
                    success=False,
                    person_id=person_id,
                    encoding_id="",
                    face_detected=False,
                    face_confidence=0.0,
                    quality_score=0.0,
                    total_encodings=person.face_encoding_count,
                    message="No face detected in image",
                    error="No face detected in image",
                )

            # Calculate confidence for detected face
            face_area_percentage = encoding_result.get("face_area_percentage", 0)
            face_confidence = min(1.0, face_area_percentage * 2)  # Normalize to 0-1

            # Create face image record
            image_id = str(uuid4())
            image = await self.image_repo.create(
                image_id=image_id,
                person_id=person_id,
                filename=f"{person_id}_face_{image_id}.jpg",
                file_path=f"persons/{person_id}/faces/{image_id}.jpg",
                file_size=len(frame_bytes),
                mime_type="image/jpeg",
                image_width=encoding_result.get("image_size", {}).get("width"),
                image_height=encoding_result.get("image_size", {}).get("height"),
                quality_score=quality_score,
                face_detected=True,
                face_confidence=face_confidence,
                is_primary=is_primary,
            )

            # Create face encoding record
            encoding_id = str(uuid4())
            face_encoding = await self.encoding_repo.create(
                encoding_id=encoding_id,
                person_id=person_id,
                encoding=encoding_result["encoding"],
                encoding_model="dlib_128d",
                confidence=face_confidence,
                quality_score=quality_score,
                source_image_id=image_id,
                is_active=True,
            )

            # Update person's face encoding count
            total_encodings = person.face_encoding_count + 1
            await self.repo.update(
                person_id,
                face_encoding_count=total_encodings,
                last_face_enrolled=__import__("datetime").datetime.utcnow(),
            )

            logger.info(f"Enrolled face for person {person_id} - encoding {encoding_id}")

            return PersonEnrollmentResponse(
                success=True,
                person_id=person_id,
                encoding_id=encoding_id,
                face_detected=True,
                face_confidence=face_confidence,
                quality_score=quality_score or 0.0,
                total_encodings=total_encodings,
                message="Face enrolled successfully",
                error=None,
            )

        except NotFoundError as e:
            logger.error(f"Error enrolling face: {e}")
            return PersonEnrollmentResponse(
                success=False,
                person_id=person_id,
                encoding_id="",
                face_detected=False,
                face_confidence=0.0,
                quality_score=0.0,
                total_encodings=0,
                message="Error enrolling face",
                error=str(e),
            )

    # =========================================================================
    # Face Recognition Methods
    # =========================================================================

    async def find_person_by_face(
        self,
        frame_data: str,
        confidence_threshold: float = 0.7,
    ) -> PersonSearchByFaceResponse:
        """
        Find person(s) by face.

        Args:
            frame_data: Base64 encoded face image
            confidence_threshold: Minimum confidence threshold (0.0-1.0)

        Returns:
            Search response with matched persons
        """
        try:
            # Decode frame
            frame_bytes = base64.b64decode(frame_data)

            # Extract encoding
            encoding_result = self.face_service.extract_face_encoding(frame_bytes)

            if not encoding_result:
                return PersonSearchByFaceResponse(
                    matches=[],
                    best_match=None,
                    total_matches=0,
                )

            face_encoding = encoding_result["encoding"]

            # Get all active encodings
            all_encodings = await self.encoding_repo.get_all_active()

            if not all_encodings:
                return PersonSearchByFaceResponse(
                    matches=[],
                    best_match=None,
                    total_matches=0,
                )

            # Match against all encodings
            matches = []
            for db_encoding in all_encodings:
                match_result = self.face_service.compare_face_encodings(
                    face_encoding,
                    db_encoding.encoding,
                )

                # Calculate confidence (inverted distance)
                confidence = max(0.0, 1.0 - match_result)

                if confidence >= confidence_threshold:
                    person = db_encoding.person
                    matches.append(
                        {
                            "person_id": person.id,
                            "person_name": f"{person.first_name} {person.last_name}",
                            "match_confidence": confidence,
                            "encoding_id": db_encoding.id,
                            "distance": match_result,
                        }
                    )

            # Sort by confidence (highest first)
            matches.sort(key=lambda x: x["match_confidence"], reverse=True)

            # Get best match
            best_match = None
            if matches:
                best = matches[0]
                best_match = {
                    "person_id": best["person_id"],
                    "person_name": best["person_name"],
                    "match_confidence": best["match_confidence"],
                    "encoding_id": best["encoding_id"],
                }

            response_matches = [
                {
                    "person_id": m["person_id"],
                    "person_name": m["person_name"],
                    "match_confidence": m["match_confidence"],
                    "encoding_id": m["encoding_id"],
                }
                for m in matches
            ]

            logger.info(f"Face search completed: {len(matches)} matches found")

            return PersonSearchByFaceResponse(
                matches=response_matches,
                best_match=best_match,
                total_matches=len(matches),
            )

        except Exception as e:
            logger.error(f"Error searching by face: {e}")
            return PersonSearchByFaceResponse(
                matches=[],
                best_match=None,
                total_matches=0,
            )

    # =========================================================================
    # Statistics Methods
    # =========================================================================

    async def get_person_summary(self) -> dict:
        """Get person system summary."""
        total = await self.repo.count_all()
        active = await self.repo.count_by_status("active")
        with_faces = await self.repo.count_with_face_encodings()
        by_type = {}

        persons = await self.repo.get_all()
        for person in persons:
            ptype = person.person_type
            by_type[ptype] = by_type.get(ptype, 0) + 1

        return {
            "total_persons": total,
            "active_persons": active,
            "inactive_persons": total - active,
            "persons_with_faces": with_faces,
            "by_type": by_type,
        }
