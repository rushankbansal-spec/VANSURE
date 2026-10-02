"""Security module for authentication, authorization, and password handling."""

import logging
import secrets
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from jose import JWTError, jwt
from passlib.hash import argon2
from passlib.exc import VerificationError
from pydantic import BaseModel

from app.core.config import get_jwt_settings, get_password_settings

logger = logging.getLogger(__name__)


class Role(str, Enum):
    """User roles in the system."""

    SUPER_ADMIN = "super_admin"
    SCHOOL_OWNER = "school_owner"
    SCHOOL_ADMIN = "school_admin"
    TRANSPORT_MANAGER = "transport_manager"
    DRIVER = "driver"
    PARENT = "parent"
    STUDENT = "student"
    FLEET_STAFF = "fleet_staff"
    ACCOUNTANT = "accountant"


class Permission(str, Enum):
    """Permission constants."""

    # Schools
    SCHOOL_READ = "school:read"
    SCHOOL_WRITE = "school:write"
    SCHOOL_ADMIN_ACCESS = "school:admin_access"

    # Students
    STUDENT_READ = "student:read"
    STUDENT_WRITE = "student:write"
    STUDENT_ENROLL = "student:enroll"

    # Vehicles
    VEHICLE_READ = "vehicle:read"
    VEHICLE_WRITE = "vehicle:write"
    VEHICLE_ASSIGN = "vehicle:assign"

    # Drivers
    DRIVER_READ = "driver:read"
    DRIVER_WRITE = "driver:write"
    DRIVER_ASSIGN = "driver:assign"

    # Routes
    ROUTE_READ = "route:read"
    ROUTE_WRITE = "route:write"
    ROUTE_OPTIMIZE = "route:optimize"

    # Trips
    TRIP_READ = "trip:read"
    TRIP_WRITE = "trip:write"
    TRIP_START = "trip:start"
    TRIP_COMPLETE = "trip:complete"
    TRIP_LOCATION = "trip:location"

    # Attendance
    ATTENDANCE_RECORD = "attendance:record"
    ATTENDANCE_VIEW = "attendance:view"

    # Notifications
    NOTIFICATION_READ = "notification:read"
    NOTIFICATION_SEND = "notification:send"

    # Billing
    BILLING_READ = "billing:read"
    BILLING_WRITE = "billing:write"
    PAYMENT_PROCESS = "payment:process"


class RoleDefinition(BaseModel):
    """Defines the permissions for a role."""

    name: str
    permissions: list[Permission]
    description: str


# Role definitions with their permissions
ROLE_DEFINITIONS: dict[Role, RoleDefinition] = {
    Role.SUPER_ADMIN: RoleDefinition(
        name=Role.SUPER_ADMIN.value,
        permissions=[
            Permission.SCHOOL_READ,
            Permission.SCHOOL_WRITE,
            Permission.SCHOOL_ADMIN_ACCESS,
            Permission.STUDENT_READ,
            Permission.STUDENT_WRITE,
            Permission.VEHICLE_READ,
            Permission.VEHICLE_WRITE,
            Permission.DRIVER_READ,
            Permission.DRIVER_WRITE,
            Permission.ROUTE_READ,
            Permission.ROUTE_WRITE,
            Permission.TRIP_READ,
            Permission.TRIP_WRITE,
            Permission.TRIP_START,
            Permission.TRIP_COMPLETE,
            Permission.TRIP_LOCATION,
            Permission.ATTENDANCE_RECORD,
            Permission.ATTENDANCE_VIEW,
            Permission.NOTIFICATION_READ,
            Permission.NOTIFICATION_SEND,
            Permission.BILLING_READ,
            Permission.BILLING_WRITE,
            Permission.PAYMENT_PROCESS,
        ],
        description="Platform super administrator with full access",
    ),
    Role.SCHOOL_OWNER: RoleDefinition(
        name=Role.SCHOOL_OWNER.value,
        permissions=[
            Permission.SCHOOL_READ,
            Permission.SCHOOL_WRITE,
            Permission.STUDENT_READ,
            Permission.STUDENT_WRITE,
            Permission.VEHICLE_READ,
            Permission.VEHICLE_WRITE,
            Permission.DRIVER_READ,
            Permission.DRIVER_WRITE,
            Permission.ROUTE_READ,
            Permission.ROUTE_WRITE,
            Permission.TRIP_READ,
            Permission.TRIP_WRITE,
            Permission.TRIP_START,
            Permission.TRIP_COMPLETE,
            Permission.TRIP_LOCATION,
            Permission.ATTENDANCE_RECORD,
            Permission.ATTENDANCE_VIEW,
            Permission.NOTIFICATION_READ,
            Permission.NOTIFICATION_SEND,
            Permission.BILLING_READ,
            Permission.BILLING_WRITE,
        ],
        description="Owner of a school with administrative privileges",
    ),
    Role.SCHOOL_ADMIN: RoleDefinition(
        name=Role.SCHOOL_ADMIN.value,
        permissions=[
            Permission.STUDENT_READ,
            Permission.STUDENT_WRITE,
            Permission.VEHICLE_READ,
            Permission.DRIVER_READ,
            Permission.ROUTE_READ,
            Permission.TRIP_READ,
            Permission.TRIP_START,
            Permission.TRIP_COMPLETE,
            Permission.ATTENDANCE_RECORD,
            Permission.ATTENDANCE_VIEW,
            Permission.NOTIFICATION_READ,
            Permission.NOTIFICATION_SEND,
        ],
        description="School administrator",
    ),
    Role.TRANSPORT_MANAGER: RoleDefinition(
        name=Role.TRANSPORT_MANAGER.value,
        permissions=[
            Permission.STUDENT_READ,
            Permission.VEHICLE_READ,
            Permission.DRIVER_READ,
            Permission.ROUTE_READ,
            Permission.TRIP_READ,
            Permission.TRIP_WRITE,
            Permission.TRIP_START,
            Permission.TRIP_COMPLETE,
            Permission.TRIP_LOCATION,
            Permission.ATTENDANCE_RECORD,
            Permission.ATTENDANCE_VIEW,
            Permission.NOTIFICATION_SEND,
        ],
        description="Transport manager for route planning and trip management",
    ),
    Role.DRIVER: RoleDefinition(
        name=Role.DRIVER.value,
        permissions=[
            Permission.TRIP_READ,
            Permission.TRIP_WRITE,
            Permission.TRIP_START,
            Permission.TRIP_COMPLETE,
            Permission.TRIP_LOCATION,
            Permission.ATTENDANCE_RECORD,
            Permission.ATTENDANCE_VIEW,
        ],
        description="Bus driver with trip and attendance permissions",
    ),
    Role.PARENT: RoleDefinition(
        name=Role.PARENT.value,
        permissions=[
            Permission.STUDENT_READ,
            Permission.TRIP_READ,
            Permission.TRIP_LOCATION,
            Permission.ATTENDANCE_VIEW,
            Permission.NOTIFICATION_READ,
        ],
        description="Parent/guardian with restricted access to their children",
    ),
    Role.STUDENT: RoleDefinition(
        name=Role.STUDENT.value,
        permissions=[
            Permission.STUDENT_READ,
            Permission.TRIP_READ,
            Permission.TRIP_LOCATION,
        ],
        description="Student with read-only access to their own information",
    ),
    Role.FLEET_STAFF: RoleDefinition(
        name=Role.FLEET_STAFF.value,
        permissions=[
            Permission.VEHICLE_READ,
            Permission.VEHICLE_WRITE,
            Permission.DRIVER_READ,
            Permission.NOTIFICATION_READ,
        ],
        description="Fleet maintenance staff",
    ),
    Role.ACCOUNTANT: RoleDefinition(
        name=Role.ACCOUNTANT.value,
        permissions=[
            Permission.SCHOOL_READ,
            Permission.STUDENT_READ,
            Permission.VEHICLE_READ,
            Permission.TRIP_READ,
            Permission.BILLING_READ,
            Permission.BILLING_WRITE,
        ],
        description="School accountant",
    ),
}


class TokenData(BaseModel):
    """Data stored in JWT tokens."""

    sub: str  # User ID
    school_id: str | None = None  # Current tenant context
    role: Role
    token_type: str = "access"  # "access" or "refresh"
    jti: str | None = None  # JWT ID for revocation
    exp: datetime | None = None


class PasswordHasher:
    """Argon2id password hasher with configurable parameters."""

    def __init__(self, settings: dict[str, Any] | None = None):
        """Initialize password hasher with settings."""
        settings = settings or {}
        self.memory_cost = settings.get("memory_cost", 65536)
        self.time_cost = settings.get("time_cost", 3)
        self.parallelism = settings.get("parallelism", 4)
        self.salt_length = settings.get("salt_length", 16)
        self.hash_length = settings.get("hash_length", 32)

    def hash(self, password: str) -> str:
        """Hash a password using Argon2id."""
        return argon2.using(
            memory_cost=self.memory_cost,
            time_cost=self.time_cost,
            parallelism=self.parallelism,
        ).hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        try:
            return argon2.verify(password_hash, password)
        except VerificationError:
            return False


class JWTService:
    """Service for JWT token creation and validation."""

    def __init__(self):
        """Initialize JWT service with settings."""
        jwt_settings = get_jwt_settings()
        self.secret_key = jwt_settings.secret_key
        self.algorithm = jwt_settings.algorithm
        self.access_token_expiration = jwt_settings.access_token_expiration
        self.refresh_token_expiration = jwt_settings.refresh_token_expiration
        self.audience = jwt_settings.audience
        self.issuer = jwt_settings.issuer

    def _create_token(
        self,
        *,
        user_id: str,
        school_id: str | None,
        role: Role,
        token_type: str,
        expires_delta: timedelta,
    ) -> str:
        """Create a JWT token."""
        now = datetime.utcnow()
        expire = now + expires_delta

        to_encode: dict[str, Any] = {
            "sub": user_id,
            "school_id": school_id,
            "role": role.value,
            "token_type": token_type,
            "iat": now,
            "exp": expire,
            "jti": secrets.token_urlsafe(16),
        }

        encoded_jwt = jwt.encode(
            to_encode,
            self.secret_key,
            algorithm=self.algorithm,
        )

        return encoded_jwt

    def create_access_token(
        self,
        *,
        user_id: str,
        school_id: str | None = None,
        role: Role = Role.PARENT,
    ) -> str:
        """Create an access token."""
        return self._create_token(
            user_id=user_id,
            school_id=school_id,
            role=role,
            token_type="access",
            expires_delta=timedelta(seconds=self.access_token_expiration),
        )

    def create_refresh_token(
        self,
        *,
        user_id: str,
        school_id: str | None = None,
        role: Role = Role.PARENT,
    ) -> str:
        """Create a refresh token."""
        return self._create_token(
            user_id=user_id,
            school_id=school_id,
            role=role,
            token_type="refresh",
            expires_delta=timedelta(seconds=self.refresh_token_expiration),
        )

    def decode_token(self, token: str) -> TokenData:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                audience=self.audience,
                issuer=self.issuer,
            )

            return TokenData(
                sub=payload.get("sub"),
                school_id=payload.get("school_id"),
                role=Role(payload.get("role")),
                token_type=payload.get("token_type", "access"),
                jti=payload.get("jti"),
                exp=datetime.fromtimestamp(payload.get("exp", 0)),
            )
        except JWTError as e:
            logger.warning(f"JWT decode error: {e}")
            raise ValueError("Invalid token") from e


def check_permission(required: Permission, user_permissions: set[Permission]) -> bool:
    """Check if user has required permission."""
    return required in user_permissions


def get_role_permissions(role: Role) -> set[Permission]:
    """Get all permissions for a role."""
    definition = ROLE_DEFINITIONS.get(role)
    return set(definition.permissions) if definition else set()


# Convenience functions
def get_password_hasher(settings: dict[str, Any] | None = None) -> PasswordHasher:
    """Get password hasher with settings."""
    password_settings = get_password_settings()
    return PasswordHasher(
        settings={
            "memory_cost": password_settings.memory_cost,
            "time_cost": password_settings.time_cost,
            "parallelism": password_settings.parallelism,
        }
    )