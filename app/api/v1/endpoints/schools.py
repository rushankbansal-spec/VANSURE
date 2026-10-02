"""School management endpoints."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.permissions import (
    get_current_user,
    require_role,
)
from app.core.security import Role

# Request models
class SchoolCreateRequest(BaseModel):
    """Create school request model."""

    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=50)
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    timezone: str = "UTC"


class SchoolUpdateRequest(BaseModel):
    """Update school request model."""

    name: str | None = Field(None, min_length=1, max_length=200)
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    timezone: str | None = None
    is_active: bool | None = None


# Response models
class SchoolResponse(BaseModel):
    """School response model."""

    id: str
    name: str
    code: str
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    timezone: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str
    detail: dict[str, Any] | None = None


# Create router
schools_router = APIRouter()


@schools_router.get(
    "/",
    response_model=list[SchoolResponse],
    status_code=status.HTTP_200_OK,
    summary="List schools",
)
async def list_schools(current_user: dict = Depends(get_current_user)) -> list[SchoolResponse]:
    """List all schools (super admin only)."""
    # Check if user is super admin
    user_role = current_user.get("role")
    if not isinstance(user_role, Role) or user_role != Role.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required",
        )
    # TODO: Implement with tenant filtering
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="List schools endpoint not yet implemented",
    )


@schools_router.get(
    "/{school_id}",
    response_model=SchoolResponse,
    status_code=status.HTTP_200_OK,
    summary="Get school by ID",
)
async def get_school(
    school_id: str,
    current_user: dict = Depends(get_current_user),
) -> SchoolResponse:
    """Get school by ID."""
    # TODO: Implement with tenant access check
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Get school endpoint not yet implemented",
    )


@schools_router.post(
    "/",
    response_model=SchoolResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create school",
    dependencies=[Depends(require_role(Role.SUPER_ADMIN))],
)
async def create_school(request: SchoolCreateRequest) -> SchoolResponse:
    """Create a new school (super admin only)."""
    # TODO: Implement school creation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Create school endpoint not yet implemented",
    )


@schools_router.put(
    "/{school_id}",
    response_model=SchoolResponse,
    status_code=status.HTTP_200_OK,
    summary="Update school",
)
async def update_school(
    school_id: str,
    request: SchoolUpdateRequest,
    current_user: dict = Depends(get_current_user),
) -> SchoolResponse:
    """Update school."""
    # TODO: Implement school update
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Update school endpoint not yet implemented",
    )


@schools_router.delete(
    "/{school_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete school",
    dependencies=[Depends(require_role(Role.SUPER_ADMIN))],
)
async def delete_school(school_id: str) -> MessageResponse:
    """Delete school (super admin only)."""
    # TODO: Implement school deletion
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Delete school endpoint not yet implemented",
    )