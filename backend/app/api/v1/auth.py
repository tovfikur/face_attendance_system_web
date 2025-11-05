"""
Authentication endpoints.
"""

import json
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.deps import CurrentUser, get_current_user
from app.core.errors import AuthenticationError
from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password, verify_token
from app.db.session import get_db
from app.models.user import User, UserSession, Role
from app.schemas.common import ErrorDetail, ErrorResponse, SuccessResponse
from app.schemas.user import (
    ChangePasswordRequest,
    CurrentUserResponse,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserResponse,
    RoleResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=SuccessResponse[LoginResponse], status_code=status.HTTP_200_OK)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)) -> SuccessResponse[LoginResponse]:
    """
    User login endpoint.

    Returns access token, refresh token, and user information.
    """
    # Find user by email
    result = await db.execute(select(User).where(User.email == request.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Get user role and permissions
    role_result = await db.execute(select(Role).where(Role.id == user.role_id))
    role = role_result.scalar_one_or_none()

    permissions = json.loads(role.permissions) if role else []

    # Create tokens
    access_token = create_access_token(
        data={
            "sub": user.id,
            "email": user.email,
            "role_id": user.role_id,
            "permissions": json.dumps(permissions),
        }
    )

    refresh_token = create_refresh_token(
        data={
            "sub": user.id,
            "email": user.email,
            "role_id": user.role_id,
            "permissions": json.dumps(permissions),
        }
    )

    # Store refresh token in database
    token_expiry = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    session = UserSession(
        user_id=user.id,
        refresh_token=refresh_token,
        expires_at=token_expiry,
    )
    db.add(session)
    await db.commit()

    # Update last_active
    user.last_active = datetime.utcnow()
    await db.commit()

    return SuccessResponse(
        data=LoginResponse(
            accessToken=access_token,
            refreshToken=refresh_token,
            user=UserResponse(
                id=user.id,
                name=user.name,
                email=user.email,
                roleId=user.role_id,
                status=user.status,
                lastActive=user.last_active,
                createdAt=user.created_at,
                updatedAt=user.updated_at,
            ),
        )
    )


@router.post("/refresh", response_model=SuccessResponse[TokenResponse], status_code=status.HTTP_200_OK)
async def refresh(request: RefreshTokenRequest, db: AsyncSession = Depends(get_db)) -> SuccessResponse[TokenResponse]:
    """
    Refresh access token using refresh token.

    Returns new access and refresh tokens.
    """
    try:
        payload = verify_token(request.refreshToken)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    # Verify refresh token exists in database and hasn't expired
    result = await db.execute(
        select(UserSession).where(
            (UserSession.refresh_token == request.refreshToken)
            & (UserSession.expires_at > datetime.utcnow())
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Get user and role
    user_result = await db.execute(select(User).where(User.id == session.user_id))
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    role_result = await db.execute(select(Role).where(Role.id == user.role_id))
    role = role_result.scalar_one_or_none()

    permissions = json.loads(role.permissions) if role else []

    # Create new tokens
    new_access_token = create_access_token(
        data={
            "sub": user.id,
            "email": user.email,
            "role_id": user.role_id,
            "permissions": json.dumps(permissions),
        }
    )

    new_refresh_token = create_refresh_token(
        data={
            "sub": user.id,
            "email": user.email,
            "role_id": user.role_id,
            "permissions": json.dumps(permissions),
        }
    )

    # Update refresh token in database (revoke old, create new)
    db.delete(session)
    new_session = UserSession(
        user_id=user.id,
        refresh_token=new_refresh_token,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(new_session)
    await db.commit()

    return SuccessResponse(
        data=TokenResponse(
            accessToken=new_access_token,
            refreshToken=new_refresh_token,
            tokenType="bearer",
            expiresIn=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: LogoutRequest, db: AsyncSession = Depends(get_db)):
    """
    User logout endpoint.

    Revokes the refresh token.
    """
    # Delete refresh token from database
    result = await db.execute(select(UserSession).where(UserSession.refresh_token == request.refreshToken))
    session = result.scalar_one_or_none()

    if session:
        db.delete(session)
        await db.commit()

    return None


@router.get("/me", response_model=SuccessResponse[CurrentUserResponse], status_code=status.HTTP_200_OK)
async def get_me(
    current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> SuccessResponse[CurrentUserResponse]:
    """
    Get current user information.

    Returns user details and permissions.
    """
    # Get user from database
    result = await db.execute(select(User).where(User.id == current_user.user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return SuccessResponse(
        data=CurrentUserResponse(
            user=UserResponse(
                id=user.id,
                name=user.name,
                email=user.email,
                roleId=user.role_id,
                status=user.status,
                lastActive=user.last_active,
                createdAt=user.created_at,
                updatedAt=user.updated_at,
            ),
            permissions=current_user.permissions,
        )
    )


@router.patch("/password", status_code=status.HTTP_200_OK)
async def change_password(
    request: ChangePasswordRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change user password."""
    if request.newPassword != request.confirmPassword:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match",
        )

    # Get user
    result = await db.execute(select(User).where(User.id == current_user.user_id))
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.currentPassword, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid current password",
        )

    # Update password
    user.hashed_password = hash_password(request.newPassword)
    await db.commit()

    return SuccessResponse(data={"message": "Password changed successfully"})
