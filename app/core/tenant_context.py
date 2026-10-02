"""Tenant context management for multi-tenancy support.

Manages tenant context propagation through the request lifecycle,
database operations, and background jobs.
"""

import contextvars
from contextvars import ContextVar
from typing import Any, Optional

# Context variable to store tenant ID in async context
tenant_id_var: ContextVar[Optional[str]] = ContextVar(
    "tenant_id", default=None
)

# Store user ID for audit purposes (optional)
user_id_var: ContextVar[Optional[str]] = ContextVar(
    "user_id", default=None
)


class TenantContext:
    """Manages tenant context for the current request/sync/async context."""

    @classmethod
    def set_tenant(cls, tenant_id: str, user_id: Optional[str] = None) -> None:
        """Set the current tenant context.

        Args:
            tenant_id: The tenant/school ID
            user_id: Optional user ID for audit purposes
        """
        tenant_id_var.set(tenant_id)
        if user_id:
            user_id_var.set(user_id)

    @classmethod
    def get_tenant(cls) -> Optional[str]:
        """Get the current tenant ID from context.

        Returns:
            The tenant ID or None if not set
        """
        return tenant_id_var.get()

    @classmethod
    def get_user(cls) -> Optional[str]:
        """Get the current user ID from context.

        Returns:
            The user ID or None if not set
        """
        return user_id_var.get()

    @classmethod
    def clear(cls) -> None:
        """Clear the tenant context (useful for testing)."""
        tenant_id_var.set(None)
        user_id_var.set(None)

    @classmethod
    def reset(cls) -> None:
        """Reset tenant context to default values."""
        cls.clear()


# Convenience function for database queries
def get_tenant_id() -> str:
    """Get tenant ID, raising error if not set.
    
    Use in database queries to ensure tenant isolation.
    """
    tenant_id = tenant_id_var.get()
    if tenant_id is None:
        raise RuntimeError("Tenant context not set")
    return tenant_id


def get_current_user_id() -> Optional[str]:
    """Get the current user ID from context."""
    return user_id_var.get()


class TenantScopedQuery:
    """Mixin/helper for tenant-scoped database queries.

    Usage:
        class StudentRepository:
            async def get_by_id(self, student_id: str) -> Student:
                tenant_id = get_tenant_id()
                return await self.session.get(Student, student_id)
    """

    def with_tenant_filter(self, query: Any, tenant_field: str = "school_id") -> Any:
        """Add tenant filter to a SQLAlchemy query.

        Args:
            query: SQLAlchemy query object
            tenant_field: Name of the tenant field (default: 'school_id')

        Returns:
            Query with tenant filter applied
        """
        tenant_id = get_tenant_id()
        return query.filter(getattr(query.model, tenant_field) == tenant_id)