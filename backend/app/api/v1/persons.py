"""Person management endpoints."""

import base64
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_current_user
from app.core.errors import NotFoundError, ValidationError
from app.db.session import get_db
from app.schemas.common import PaginatedResponse, PaginationMeta, SuccessResponse
from app.schemas.person import (
    PersonCreate,
    PersonEnrollmentRequest,
    PersonEnrollmentResponse,
    PersonResponse,
    PersonSearchByFaceRequest,
    PersonSearchByFaceResponse,
    PersonSearchRequest,
    PersonUpdate,
)
from app.services.person_service import PersonService

router = APIRouter(tags=["Persons"])
logger = logging.getLogger(__name__)


# Helper functions
async def get_person_service(db: AsyncSession = Depends(get_db)) -> PersonService:
    """Get person service."""
    return PersonService(db)


# ============================================================================
# Person CRUD Endpoints
# ============================================================================


@router.post("", response_model=SuccessResponse[PersonResponse], status_code=status.HTTP_201_CREATED)
async def create_person(
    request: PersonCreate,
    current_user: CurrentUser = Depends(get_current_user),
    service: PersonService = Depends(get_person_service),
) -> SuccessResponse[PersonResponse]:
    """Create a new person."""
    if not current_user.has_permission("persons:write"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create persons",
        )

    try:
        person = await service.create_person(request)
        return SuccessResponse(
            data=PersonResponse(
                id=person.id,
                first_name=person.first_name,
                last_name=person.last_name,
                email=person.email,
                phone=person.phone,
                person_type=person.person_type,
                id_number=person.id_number,
                id_type=person.id_type,
                department=person.department,
                organization=person.organization,
                status=person.status,
                face_encoding_count=person.face_encoding_count,
                enrolled_at=person.enrolled_at,
                last_face_enrolled=person.last_face_enrolled,
                createdAt=person.created_at,
                updatedAt=person.updated_at,
            ),
            meta={"created": True},
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=PaginatedResponse[PersonResponse])
async def list_persons(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    status: Optional[str] = Query(None, description="Filter by status"),
    person_type: Optional[str] = Query(None, description="Filter by type"),
    department: Optional[str] = Query(None, description="Filter by department"),
    current_user: CurrentUser = Depends(get_current_user),
    service: PersonService = Depends(get_person_service),
) -> PaginatedResponse[PersonResponse]:
    """List persons with optional filtering."""
    if not current_user.has_permission("persons:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view persons",
        )

    skip = (page - 1) * page_size
    persons = await service.list_persons(
        skip=skip,
        limit=page_size,
        status=status,
        person_type=person_type,
        department=department,
    )

    # Get total count
    total = len(persons) + skip  # Simplified, in production would query count
    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        data=[
            PersonResponse(
                id=p.id,
                first_name=p.first_name,
                last_name=p.last_name,
                email=p.email,
                phone=p.phone,
                person_type=p.person_type,
                id_number=p.id_number,
                id_type=p.id_type,
                department=p.department,
                organization=p.organization,
                status=p.status,
                face_encoding_count=p.face_encoding_count,
                enrolled_at=p.enrolled_at,
                last_face_enrolled=p.last_face_enrolled,
                createdAt=p.created_at,
                updatedAt=p.updated_at,
            )
            for p in persons
        ],
        meta=PaginationMeta(page=page, pageSize=page_size, total=total, totalPages=total_pages),
    )


@router.get("/{person_id}", response_model=SuccessResponse[PersonResponse])
async def get_person(
    person_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: PersonService = Depends(get_person_service),
) -> SuccessResponse[PersonResponse]:
    """Get person by ID."""
    if not current_user.has_permission("persons:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view persons",
        )

    try:
        person = await service.get_person(person_id)
        return SuccessResponse(
            data=PersonResponse(
                id=person.id,
                first_name=person.first_name,
                last_name=person.last_name,
                email=person.email,
                phone=person.phone,
                person_type=person.person_type,
                id_number=person.id_number,
                id_type=person.id_type,
                department=person.department,
                organization=person.organization,
                status=person.status,
                face_encoding_count=person.face_encoding_count,
                enrolled_at=person.enrolled_at,
                last_face_enrolled=person.last_face_enrolled,
                createdAt=person.created_at,
                updatedAt=person.updated_at,
            )
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{person_id}", response_model=SuccessResponse[PersonResponse])
async def update_person(
    person_id: str,
    request: PersonUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    service: PersonService = Depends(get_person_service),
) -> SuccessResponse[PersonResponse]:
    """Update person."""
    if not current_user.has_permission("persons:write"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to manage persons",
        )

    try:
        person = await service.update_person(person_id, request)
        return SuccessResponse(
            data=PersonResponse(
                id=person.id,
                first_name=person.first_name,
                last_name=person.last_name,
                email=person.email,
                phone=person.phone,
                person_type=person.person_type,
                id_number=person.id_number,
                id_type=person.id_type,
                department=person.department,
                organization=person.organization,
                status=person.status,
                face_encoding_count=person.face_encoding_count,
                enrolled_at=person.enrolled_at,
                last_face_enrolled=person.last_face_enrolled,
                createdAt=person.created_at,
                updatedAt=person.updated_at,
            )
        )
    except (NotFoundError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if isinstance(e, NotFoundError) else status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person(
    person_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: PersonService = Depends(get_person_service),
):
    """Delete person."""
    if not current_user.has_permission("persons:write"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to manage persons",
        )

    try:
        await service.delete_person(person_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# Face Enrollment Endpoints
# ============================================================================


@router.post("/{person_id}/enroll", response_model=SuccessResponse[PersonEnrollmentResponse])
async def enroll_face(
    person_id: str,
    request: PersonEnrollmentRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: PersonService = Depends(get_person_service),
) -> SuccessResponse[PersonEnrollmentResponse]:
    """Enroll a face for a person."""
    if not current_user.has_permission("persons:write"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to enroll faces",
        )

    result = await service.enroll_face(
        person_id=person_id,
        frame_data=request.frame_data,
        is_primary=request.is_primary,
        quality_score=request.quality_score,
    )

    return SuccessResponse(data=result)


# ============================================================================
# Face Search Endpoints
# ============================================================================


@router.post(
    "/search/by-face",
    response_model=SuccessResponse[PersonSearchByFaceResponse],
)
async def search_by_face(
    request: PersonSearchByFaceRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: PersonService = Depends(get_person_service),
) -> SuccessResponse[PersonSearchByFaceResponse]:
    """Find person by face."""
    if not current_user.has_permission("persons:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to search persons",
        )

    result = await service.find_person_by_face(
        frame_data=request.frame_data,
        confidence_threshold=request.confidence_threshold,
    )

    return SuccessResponse(data=result)


@router.get("/search", response_model=PaginatedResponse[PersonResponse])
async def search_persons(
    q: str = Query(..., description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: CurrentUser = Depends(get_current_user),
    service: PersonService = Depends(get_person_service),
) -> PaginatedResponse[PersonResponse]:
    """Search persons by name, email, or ID."""
    if not current_user.has_permission("persons:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to search persons",
        )

    persons = await service.search_persons(q)

    # Apply pagination
    skip = (page - 1) * page_size
    paginated = persons[skip : skip + page_size]
    total = len(persons)
    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        data=[
            PersonResponse(
                id=p.id,
                first_name=p.first_name,
                last_name=p.last_name,
                email=p.email,
                phone=p.phone,
                person_type=p.person_type,
                id_number=p.id_number,
                id_type=p.id_type,
                department=p.department,
                organization=p.organization,
                status=p.status,
                face_encoding_count=p.face_encoding_count,
                enrolled_at=p.enrolled_at,
                last_face_enrolled=p.last_face_enrolled,
                createdAt=p.created_at,
                updatedAt=p.updated_at,
            )
            for p in paginated
        ],
        meta=PaginationMeta(page=page, pageSize=page_size, total=total, totalPages=total_pages),
    )


# ============================================================================
# Summary Endpoints
# ============================================================================


@router.get("/summary", response_model=SuccessResponse[dict])
async def get_person_summary(
    current_user: CurrentUser = Depends(get_current_user),
    service: PersonService = Depends(get_person_service),
) -> SuccessResponse[dict]:
    """Get person system summary."""
    if not current_user.has_permission("persons:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view persons",
        )

    summary = await service.get_person_summary()
    return SuccessResponse(data=summary)
