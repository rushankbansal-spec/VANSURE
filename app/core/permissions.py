"""Permission checking utilities and dependencies."""

from datetime import datetime
from functools import wraps
from typing import Callable, Any, TypeVar

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AuthorizationException,
    ErrorCode,
    TenantAccessException,
)
from app.core.security import (
    JWTService,
    Permission,
    Role,
    get_role_permissions,
    check_permission,
)
from app.core.tenant_context import TenantContext, get_tenant_id
from app.infrastructure.database import get_session

T = TypeVar("T")

# HTTP Bearer token scheme
bearer_scheme = HTTPBearer(auto_error=False)


class Permissions:
    """Permission checking class."""

    def __init__(self, required_permission: Permission | list[Permission]):
        """Initialize with required permission(s).

        Args:
            required_permission: Single permission or list of permissions (OR logic)
        """
        self.permissions = (
            [required_permission]
            if isinstance(required_permission, Permission)
            else required_permission
        )

    def has_permission(self, user_permissions: set[Permission]) -> bool:
        """Check if user has any of the required permissions.

        Args:
            user_permissions: Set of permissions the user has

        Returns:
            True if user has at least one required permission
        """
        return any(check_permission(p, user_permissions) for p in self.permissions)


def require_permission(permission: Permission | list[Permission]) -> Callable[[T], T]:
    """Decorator to require specific permission for an endpoint.

    Args:
        permission: Required permission(s)

    Returns:
        Decorated function that checks permissions
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user permissions (would come from token or session)
            # This is a simplified version - production would cache permissions
            raise NotImplementedError("Permission checking in decorators requires dependency injection")
        return wrapper
    return decorator


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> dict[str, str | int]:
    """Get the current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer token credentials
        session: Database session

    Returns:
        Dictionary with user_id, school_id, and role

    Raises:
        HTTPException: If token is invalid or missing
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    token = credentials.credentials
    jwt_service = JWTService()

    try:
        token_data = jwt_service.decode_token(token)
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )

    if token_data.token_type != "access":
        raise HTTPException(
            status_code=401,
            detail="Invalid token type",
        )

    # Check if token is expired
    if token_data.exp and token_data.exp < token_data.iat:
        raise HTTPException(
            status_code=401,
            detail="Token expired",
        )

    return {
        "user_id": token_data.sub,
        "school_id": token_data.school_id,
        "role": token_data.role,
    }


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> dict[str, str | Role]:
    """Get the current authenticated user and set tenant context.

    This is the main auth dependency that:
    1. Validates the JWT token
    2. Sets tenant context from the token
    3. Returns user info

    Args:
        request: FastAPI request
        credentials: HTTP Bearer token credentials
        session: Database session

    Returns:
        Dictionary with user_id, school_id, and role
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    token = credentials.credentials
    jwt_service = JWTService()

    try:
        token_data = jwt_service.decode_token(token)
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )

    if token_data.token_type != "access":
        raise HTTPException(
            status_code=401,
            detail="Invalid token type",
        )

    # Check token expiration
    if token_data.exp and token_data.exp < datetime.utcnow():
        raise HTTPException(
            status_code=401,
            detail="Token expired",
        )

    # Set tenant context from token
    if token_data.school_id:
        TenantContext.set_tenant(
            str(token_data.school_id),
            str(token_data.sub) if token_data.sub else None,
        )

    request.state.user_id = token_data.sub
    request.state.school_id = token_data.school_id
    request.state.role = token_data.role

    return {
        "user_id": token_data.sub,
        "school_id": token_data.school_id,
        "role": token_data.role,
    }


async def require_tenant_access(
    resource_tenant_id: str,
    current_user: dict[str, str | Role] = Depends(get_current_user),
) -> None:
    """Verify that the current user has access to the tenant of the resource.

    Args:
        resource_tenant_id: The tenant ID of the resource being accessed
        current_user: Current authenticated user

    Raises:
        TenantAccessException: If user doesn't have access to the tenant
    """
    user_school_id = current_user.get("school_id")

    if not user_school_id:
        raise TenantAccessException("No tenant context available")

    if str(user_school_id) != resource_tenant_id:
        raise TenantAccessException(
            "Access denied: You can only access resources from your tenant"
        )


def require_role(*roles: Role) -> Callable:
    """Create a dependency that requires one of the specified roles.

    Args:
        *roles: Allowed roles

    Returns:
        Dependency function
    """

    async def dependency(
        current_user: dict[str, str | Role] = Depends(get_current_user),
    ) -> dict[str, str | Role]:
        user_role = current_user.get("role")

        if user_role not in roles:
            raise AuthorizationException(
                error_code=ErrorCode.INSUFFICIENT_PERMISSIONS,
                message=f"Required role: {', '.join(r.value for r in roles)}",
            )

        return current_user

    return dependency


def require_permission_dep(
    permission: Permission | list[Permission],
) -> Callable:
    """Create a dependency that requires a specific permission.

    Args:
        permission: Required permission(s)

    Returns:
        Dependency function
    """

    async def dependency(
        current_user: dict[str, str | Role] = Depends(get_current_user),
    ) -> dict[str, str | Role]:
        user_role = current_user.get("role")

        if isinstance(user_role, Role):
            user_permissions = get_role_permissions(user_role)

            required_perms = (
                [permission] if isinstance(permission, Permission) else permission
            )

            if not any(check_permission(p, user_permissions) for p in required_perms):
                raise AuthorizationException(
                    error_code=ErrorCode.INSUFFICIENT_PERMISSIONS,
                    message=f"Required permission: {required_perms[0].value}",
                )
        else:
            # For super admin, all permissions are granted
            pass

        return current_user

    return dependency


def is_super_admin(
    current_user: dict[str, str | Role] = Depends(get_current_user),
) -> bool:
    """Check if user is a super admin.

    Args:
        current_user: Current authenticated user

    Returns:
        True if user is super admin
    """
    user_role = current_user.get("role")
    return isinstance(user_role, Role) and user_role == Role.SUPER_ADMIN


def is_school_admin_or_above(
    current_user: dict[str, str | Role] = Depends(get_current_user),
) -> bool:
    """Check if user is school admin or above.

    Args:
        current_user: Current authenticated user

    Returns:
        True if user has school admin or higher role
    """
    user_role = current_user.get("role")
    if not isinstance(user_role, Role):
        return False

    admin_roles = {
        Role.SUPER_ADMIN,
        Role.SCHOOL_OWNER,
        Role.SCHOOL_ADMIN,
        Role.ACCOUNTANT,
    }

    return user_role in admin_roles