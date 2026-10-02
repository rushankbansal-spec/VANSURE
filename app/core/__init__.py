"""Core module for VanSure backend.

This module contains cross-cutting concerns:
- Configuration management
- Security (authentication, authorization)
- Tenant context
- Middleware
- Exceptions
- Logging
"""

from app.core.config import (
    Settings,
    get_settings,
    get_database_settings,
    get_redis_settings,
    get_jwt_settings,
    get_rate_limit_settings,
    get_security_settings,
    get_logging_settings,
)
from app.core.exceptions import (
    VanSureException,
    AuthenticationException,
    AuthorizationException,
    TenantAccessException,
    BusinessLogicException,
    ErrorCode,
    raise_exception,
)
from app.core.logging import (
    setup_logging,
    get_logger,
    set_request_id,
    get_request_id,
    set_correlation_id,
    get_correlation_id,
    logger,
)
from app.core.middleware import (
    RequestIDMiddleware,
    CorrelationIDMiddleware,
    TenantContextMiddleware,
    SecurityHeadersMiddleware,
    setup_middleware,
    tenant_context,
)
from app.core.permissions import (
    Permissions,
    get_current_user,
    get_current_user_id,
    require_role,
    require_permission_dep,
    is_super_admin,
    is_school_admin_or_above,
)
from app.core.security import (
    Role,
    Permission,
    RoleDefinition,
    ROLE_DEFINITIONS,
    TokenData,
    PasswordHasher,
    JWTService,
    check_permission,
    get_role_permissions,
    get_password_hasher,
)
from app.core.tenant_context import (
    TenantContext,
    get_tenant_id,
    get_current_user_id as get_ctx_user_id,
    TenantScopedQuery,
)

__all__ = [
    # Config
    "Settings",
    "get_settings",
    "get_database_settings",
    "get_redis_settings",
    "get_jwt_settings",
    "get_rate_limit_settings",
    "get_security_settings",
    "get_logging_settings",
    # Exceptions
    "VanSureException",
    "AuthenticationException",
    "AuthorizationException",
    "TenantAccessException",
    "BusinessLogicException",
    "ErrorCode",
    "raise_exception",
    # Logging
    "setup_logging",
    "get_logger",
    "set_request_id",
    "get_request_id",
    "set_correlation_id",
    "get_correlation_id",
    "logger",
    # Middleware
    "RequestIDMiddleware",
    "CorrelationIDMiddleware",
    "TenantContextMiddleware",
    "SecurityHeadersMiddleware",
    "setup_middleware",
    "tenant_context",
    # Permissions
    "Permissions",
    "get_current_user",
    "get_current_user_id",
    "require_role",
    "require_permission_dep",
    "is_super_admin",
    "is_school_admin_or_above",
    # Security
    "Role",
    "Permission",
    "RoleDefinition",
    "ROLE_DEFINITIONS",
    "TokenData",
    "PasswordHasher",
    "JWTService",
    "check_permission",
    "get_role_permissions",
    "get_password_hasher",
    # Tenant context
    "TenantContext",
    "get_tenant_id",
    "get_ctx_user_id",
    "TenantScopedQuery",
]