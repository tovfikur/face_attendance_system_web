"""
Roles endpoint.
"""

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.models.user import Role
from app.schemas.common import SuccessResponse
from app.schemas.user import RoleResponse

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("", response_model=SuccessResponse[list[RoleResponse]])
async def get_roles(
    current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> SuccessResponse[list[RoleResponse]]:
    """
    Get all roles.

    Returns list of all roles and their permissions.
    """
    result = await db.execute(select(Role))
    roles = result.scalars().all()

    return SuccessResponse(
        data=[
            RoleResponse(
                id=role.id,
                name=role.name,
                permissions=json.loads(role.permissions) if role.permissions else [],
                description=role.description,
                createdAt=role.created_at,
                updatedAt=role.updated_at,
            )
            for role in roles
        ]
    )
