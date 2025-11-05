"""User management endpoints."""

from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import CurrentUser, get_current_user
from app.core.security import hash_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationMeta, SuccessResponse
from app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=PaginatedResponse[UserResponse])
async def list_users(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    role_id: Optional[str] = Query(None, description="Filter by role ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
) -> PaginatedResponse[UserResponse]:
    """
    List all users with pagination and filtering.

    Requires: `users:read` permission
    """
    # Check permission
    if not current_user.has_permission("users:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view users",
        )

    # Build query
    query = select(User)

    # Apply filters
    filters = []

    if search:
        search_pattern = f"%{search}%"
        filters.append(
            (User.name.ilike(search_pattern)) | (User.email.ilike(search_pattern))
        )

    if role_id:
        filters.append(User.role_id == role_id)

    if status:
        filters.append(User.status == status)

    if filters:
        from sqlalchemy import or_

        query = query.where(or_(*filters) if len(filters) > 1 else filters[0])

    # Get total count before pagination
    count_query = select(User)
    if filters:
        from sqlalchemy import or_

        count_query = count_query.where(
            or_(*filters) if len(filters) > 1 else filters[0]
        )
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Execute query
    result = await db.execute(query)
    users = result.scalars().all()

    # Convert to response schema
    user_responses = [
        UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            roleId=user.role_id,
            status=user.status,
            lastActive=user.last_active,
            createdAt=user.created_at,
            updatedAt=user.updated_at,
        )
        for user in users
    ]

    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        data=user_responses,
        meta=PaginationMeta(
            page=page, pageSize=page_size, total=total, totalPages=total_pages
        ),
    )


@router.post("", response_model=SuccessResponse[UserResponse], status_code=status.HTTP_201_CREATED)
async def create_user(
    request: UserCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[UserResponse]:
    """
    Create a new user.

    Requires: `users:write` permission
    """
    # Check permission
    if not current_user.has_permission("users:write"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create users",
        )

    # Check if email already exists
    result = await db.execute(select(User).where(User.email == request.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    # Create new user
    user = User(
        id=str(uuid4()),
        name=request.name,
        email=request.email,
        role_id=request.roleId,
        status="active",
    )

    # Set password if provided
    if request.password:
        user.hashed_password = hash_password(request.password)
    else:
        # TODO: Generate temporary password and send via email
        user.hashed_password = hash_password(str(uuid4()))

    db.add(user)
    await db.commit()
    await db.refresh(user)

    user_response = UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        roleId=user.role_id,
        status=user.status,
        lastActive=user.last_active,
        createdAt=user.created_at,
        updatedAt=user.updated_at,
    )

    return SuccessResponse(
        data=user_response,
        meta={"createdAt": user.created_at.isoformat()},
    )


@router.get("/{user_id}", response_model=SuccessResponse[UserResponse])
async def get_user(
    user_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[UserResponse]:
    """
    Get a specific user by ID.

    Requires: `users:read` permission
    """
    # Check permission
    if not current_user.has_permission("users:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view users",
        )

    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user_response = UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        roleId=user.role_id,
        status=user.status,
        lastActive=user.last_active,
        createdAt=user.created_at,
        updatedAt=user.updated_at,
    )

    return SuccessResponse(data=user_response)


@router.put("/{user_id}", response_model=SuccessResponse[UserResponse])
async def update_user(
    user_id: str,
    request: UserUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[UserResponse]:
    """
    Update a user.

    Requires: `users:write` permission
    """
    # Check permission
    if not current_user.has_permission("users:write"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update users",
        )

    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check if email is already taken by another user
    if request.email and request.email != user.email:
        result = await db.execute(
            select(User).where(
                and_(User.email == request.email, User.id != user_id)
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )

    # Update fields
    if request.name is not None:
        user.name = request.name
    if request.email is not None:
        user.email = request.email
    if request.roleId is not None:
        user.role_id = request.roleId
    if request.status is not None:
        user.status = request.status

    db.add(user)
    await db.commit()
    await db.refresh(user)

    user_response = UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        roleId=user.role_id,
        status=user.status,
        lastActive=user.last_active,
        createdAt=user.created_at,
        updatedAt=user.updated_at,
    )

    return SuccessResponse(data=user_response)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a user.

    Requires: `users:write` permission
    """
    # Check permission
    if not current_user.has_permission("users:write"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete users",
        )

    # Prevent deleting yourself
    if user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account",
        )

    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Delete user
    await db.delete(user)
    await db.commit()
