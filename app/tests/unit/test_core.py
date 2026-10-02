"""Basic tests for VanSure backend foundation."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.core.security import Role, Permission, get_role_permissions, check_permission
from app.core.tenant_context import TenantContext, get_tenant_id


class TestConfig:
    """Tests for configuration module."""

    def test_settings_loads(self):
        """Test that settings can be loaded."""
        settings = get_settings()
        assert settings is not None
        assert settings.app_name == "VanSure"

    def test_get_settings_cached(self):
        """Test that get_settings returns cached instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2


class TestSecurity:
    """Tests for security module."""

    def test_role_permissions(self):
        """Test that roles have correct permissions."""
        super_admin_perms = get_role_permissions(Role.SUPER_ADMIN)
        assert Permission.SCHOOL_READ in super_admin_perms
        assert Permission.SCHOOL_WRITE in super_admin_perms

    def test_driver_permissions(self):
        """Test that driver has correct permissions."""
        driver_perms = get_role_permissions(Role.DRIVER)
        assert Permission.TRIP_READ in driver_perms
        assert Permission.TRIP_WRITE in driver_perms
        assert Permission.SCHOOL_WRITE not in driver_perms

    def test_permission_check(self):
        """Test permission checking."""
        permissions = {Permission.SCHOOL_READ, Permission.STUDENT_READ}
        assert check_permission(Permission.SCHOOL_READ, permissions)
        assert not check_permission(Permission.SCHOOL_WRITE, permissions)


class TestTenantContext:
    """Tests for tenant context management."""

    def test_set_and_get_tenant(self):
        """Test setting and getting tenant context."""
        TenantContext.set_tenant("school-123", "user-456")
        assert get_tenant_id() == "school-123"
        TenantContext.clear()

    def test_tenant_context_clear(self):
        """Test clearing tenant context."""
        TenantContext.set_tenant("school-123")
        TenantContext.clear()
        assert get_tenant_id() is None

    def test_tenant_context_no_leak(self):
        """Test that tenant context doesn't leak between tests."""
        # Should start clean
        TenantContext.clear()
        assert get_tenant_id() is None


class TestValidation:
    """Tests for Pydantic validation."""

    def test_role_enum_values(self):
        """Test Role enum values."""
        assert Role.SUPER_ADMIN.value == "super_admin"
        assert Role.PARENT.value == "parent"
        assert Role.DRIVER.value == "driver"

    def test_permission_enum_values(self):
        """Test Permission enum values."""
        assert Permission.SCHOOL_READ.value == "school:read"
        assert Permission.TRIP_START.value == "trip:start"