"""Application exceptions with error codes."""

from enum import Enum
from typing import Any, Optional

from fastapi import HTTPException, status


class ErrorCode(str, Enum):
    """Error codes for consistent error handling."""

    # Authentication (401)
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    REFRESH_TOKEN_INVALID = "REFRESH_TOKEN_INVALID"

    # Authorization (403)
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    TENANT_ACCESS_DENIED = "TENANT_ACCESS_DENIED"
    OPERATION_NOT_ALLOWED = "OPERATION_NOT_ALLOWED"

    # Validation (422)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"

    # Business logic (400)
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    RESOURCE_IN_USE = "RESOURCE_IN_USE"
    CONSTRAINT_VIOLATION = "CONSTRAINT_VIOLATION"

    # Rate limiting (429)
    RATE_LIMITED = "RATE_LIMITED"

    # External services
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    NOTIFICATION_DELIVERY_FAILED = "NOTIFICATION_DELIVERY_FAILED"

    # GPS/Tracking (400)
    INVALID_GPS_DATA = "INVALID_GPS_DATA"
    STALE_GPS_DATA = "STALE_GPS_DATA"
    UNAUTHORIZED_DEVICE = "UNAUTHORIZED_DEVICE"

    # Trip state machine (400)
    INVALID_TRIP_STATE = "INVALID_TRIP_STATE"
    TRIP_ALREADY_STARTED = "TRIP_ALREADY_STARTED"
    TRIP_NOT_STARTED = "TRIP_NOT_STARTED"


class VanSureException(HTTPException):
    """Base exception for VanSure with error code and structured details."""

    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize the exception.

        Args:
            error_code: Enum error code
            message: Human-readable message
            status_code: HTTP status code
            detail: Additional structured details
        """
        self.error_code = error_code
        self.detail = detail or {}

        # Build structured error response
        error_response = {
            "error_code": error_code.value,
            "message": message,
        }

        if detail:
            error_response["detail"] = detail

        super().__init__(
            status_code=status_code,
            detail=error_response,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for JSON responses."""
        return {
            "error_code": self.error_code.value,
            "message": self.detail.get("message", str(self.detail)),
        }


class AuthenticationException(VanSureException):
    """Raised for authentication failures."""

    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.INVALID_CREDENTIALS,
        message: str = "Authentication failed",
        detail: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            error_code=error_code,
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )


class AuthorizationException(VanSureException):
    """Raised for authorization failures."""

    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.INSUFFICIENT_PERMISSIONS,
        message: str = "Access denied",
        detail: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            error_code=error_code,
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class TenantAccessException(AuthorizationException):
    """Raised when accessing a resource from a different tenant."""

    def __init__(
        self,
        message: str = "Access denied to this tenant's resources",
        detail: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            error_code=ErrorCode.TENANT_ACCESS_DENIED,
            message=message,
            detail=detail,
        )


class ResourceNotFoundException(AuthorizationException):
    """Raised when a resource is not found or access is denied (to prevent enumeration)."""

    def __init__(
        self,
        resource_type: str = "Resource",
        detail: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            message=f"{resource_type} not found",
            detail=detail,
        )


class BusinessLogicException(VanSureException):
    """Raised for business rule violations."""

    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.CONSTRAINT_VIOLATION,
        message: str = "Business rule violation",
        detail: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            error_code=error_code,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class TripStateException(BusinessLogicException):
    """Raised when trip state transition is invalid."""

    def __init__(
        self,
        current_state: str,
        target_state: str,
        message: Optional[str] = None,
    ) -> None:
        super().__init__(
            error_code=ErrorCode.INVALID_TRIP_STATE,
            message=message or f"Cannot transition from {current_state} to {target_state}",
            detail={"current_state": current_state, "target_state": target_state},
        )


class InvalidGPSException(BusinessLogicException):
    """Raised when GPS data is invalid."""

    def __init__(
        self,
        reason: str,
        detail: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            error_code=ErrorCode.INVALID_GPS_DATA,
            message=f"Invalid GPS data: {reason}",
            detail=detail,
        )


class StaleGPSException(BusinessLogicException):
    """Raised when GPS data is too old."""

    def __init__(
        self,
        stale_duration_seconds: int,
        threshold_seconds: int,
    ) -> None:
        super().__init__(
            error_code=ErrorCode.STALE_GPS_DATA,
            message="GPS data is stale",
            detail={
                "stale_duration_seconds": stale_duration_seconds,
                "threshold_seconds": threshold_seconds,
            },
        )


class RateLimitException(VanSureException):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
    ) -> None:
        super().__init__(
            error_code=ErrorCode.RATE_LIMITED,
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"retry_after": retry_after},
        )


class ValidationException(VanSureException):
    """Raised for validation errors."""

    def __init__(
        self,
        errors: list[dict[str, Any]],
        message: str = "Validation failed",
    ) -> None:
        super().__init__(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"errors": errors},
        )


class ExternalServiceException(VanSureException):
    """Raised for external service failures."""

    def __init__(
        self,
        service_name: str,
        message: str = "External service error",
        detail: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            message=f"{service_name}: {message}",
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"service": service_name, **(detail or {})},
        )


def raise_exception(
    error_code: ErrorCode,
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    **kwargs: Any,
) -> None:
    """Raise a VanSureException with the given parameters.

    Args:
        error_code: Error code enum
        message: Error message
        status_code: HTTP status code
        **kwargs: Additional details to include
    """
    raise VanSureException(
        error_code=error_code,
        message=message,
        status_code=status_code,
        detail=kwargs if kwargs else None,
    )