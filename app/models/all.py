"""SQLAlchemy database models for VanSure backend.

All models include:
- tenant_id on tenant-scoped tables
- created_at / updated_at timestamps
- proper indexes for tenant isolation and query performance
"""

from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from geoalchemy2 import Geography

from app.infrastructure.database import Base
from app.core.security import Role, AttendanceStatus, TripStatus, Permission


class School(Base):
    """School/tenant entity with multi-tenancy support."""

    __tablename__ = "schools"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    address: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(255))
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    language: Mapped[str] = mapped_column(String(10), default="en")
    logo_url: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Configuration fields
    working_hours_start: Mapped[str] = mapped_column(String(8), default="06:00:00")
    working_hours_end: Mapped[str] = mapped_column(String(8), default="18:00:00")
    academic_year_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    currency: Mapped[str] = mapped_column(String(3), default="USD")

    # Relationships
    memberships: Mapped[list["SchoolMembership"]] = relationship(
        "SchoolMembership", back_populates="school", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_schools_code", "code"),
        Index("ix_schools_is_active", "is_active"),
    )


class SchoolMembership(Base):
    """Association table for users and their school memberships."""

    __tablename__ = "school_memberships"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[Role] = mapped_column(SAEnum(Role), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    school: Mapped["School"] = relationship("School", back_populates="memberships")
    user: Mapped["User"] = relationship("User", back_populates="memberships")

    __table_args__ = (
        UniqueConstraint("school_id", "user_id", name="uq_school_membership_user"),
        Index("ix_memberships_school_id", "school_id"),
        Index("ix_memberships_user_id", "user_id"),
    )


class User(Base):
    """User model with authentication and RBAC."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    role: Mapped[Role] = mapped_column(SAEnum(Role), default=Role.PARENT, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    memberships: Mapped[list["SchoolMembership"]] = relationship(
        "SchoolMembership", back_populates="user", cascade="all, delete-orphan"
    )
    students: Mapped[list["Student"]] = relationship("Student", back_populates="parent", lazy="selectin")
    assigned_vehicles: Mapped[list["Vehicle"]] = relationship("Vehicle", back_populates="driver", lazy="selectin")
    trips_as_driver: Mapped[list["Trip"]] = relationship("Trip", back_populates="driver", lazy="selectin")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_users_email", "email"),)


class Student(Base):
    """Student model."""

    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    gender: Mapped[str | None] = mapped_column(String(20))
    photo_url: Mapped[str | None] = mapped_column(Text)
    medical_info: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    school: Mapped["School"] = relationship("School")


class Vehicle(Base):
    """Vehicle model."""

    __tablename__ = "vehicles"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    plate_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, default=15)
    make: Mapped[str | None] = mapped_column(String(50))
    model: Mapped[str | None] = mapped_column(String(50))
    year: Mapped[int | None] = mapped_column(Integer)
    color: Mapped[str | None] = mapped_column(String(30))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    current_latitude: Mapped[float | None] = mapped_column(Float)
    current_longitude: Mapped[float | None] = mapped_column(Float)
    current_speed: Mapped[int | None] = mapped_column(Integer)
    last_gps_update: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    school: Mapped["School"] = relationship("School")
    driver: Mapped["User | None"] = relationship("User", back_populates="assigned_vehicles", foreignkeys=[lambda: User.id])


class DriverProfile(Base):
    """Driver profile with license and verification details."""

    __tablename__ = "driver_profiles"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    license_number: Mapped[str] = mapped_column(String(50), nullable=False)
    license_state: Mapped[str] = mapped_column(String(10), nullable=False)
    license_expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    phone: Mapped[str | None] = mapped_column(String(20))
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User")


class Route(Base):
    """Route with ordered stops."""

    __tablename__ = "routes"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    distance_km: Mapped[float | None] = mapped_column(Float)
    estimated_duration_minutes: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    school: Mapped["School"] = relationship("School")
    stops: Mapped[list["RouteStop"]] = relationship("RouteStop", order_by="RouteStop.order", cascade="all, delete-orphan")
    trips: Mapped[list["Trip"]] = relationship("Trip", back_populates="route", cascade="all, delete-orphan")

    __table_args__ = (Index("ix_routes_school_id", "school_id"), Index("ix_routes_is_active", "is_active"))


class RouteStop(Base):
    """Single stop on a route."""

    __tablename__ = "route_stops"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("routes.id", ondelete="CASCADE"), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str | None] = mapped_column(Text)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_arrival_minutes: Mapped[int | None] = mapped_column(Integer)

    # Relationships
    route: Mapped["Route"] = relationship("Route", back_populates="stops")

    __table_args__ = (
        Index("ix_route_stops_route_order", "route_id", "order", unique=True),
        UniqueConstraint("route_id", "order", "latitude", "longitude", name="uq_route_stop_unique"),
    )


class Trip(Base):
    """Trip model with state machine."""

    __tablename__ = "trips"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    vehicle_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    route_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("routes.id", ondelete="SET NULL"))
    driver_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    trip_type: Mapped[str] = mapped_column(String(10), default="PICKUP")  # PICKUP or DROP
    status: Mapped[str] = mapped_column(String(20), default="NOT_STARTED", index=True)
    scheduled_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expected_duration_minutes: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    sos_activated: Mapped[bool] = mapped_column(Boolean, default=False)
    sos_activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sos_resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sos_reason: Mapped[str | None] = mapped_column(Text)
    start_latitude: Mapped[float | None] = mapped_column(Float)
    start_longitude: Mapped[float | None] = mapped_column(Float)
    end_latitude: Mapped[float | None] = mapped_column(Float)
    end_longitude: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    school: Mapped["School"] = relationship("School", back_populates="trips")
    vehicle: Mapped["Vehicle"] = relationship("Vehicle")
    route: Mapped["Route | None"] = relationship("Route")
    driver: Mapped["User | None"] = relationship("User", back_populates="trips_as_driver")
    location_updates: Mapped[list["TripLocation"]] = relationship("TripLocation", back_populates="trip", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_trips_school_id_status", "school_id", "status"),
        Index("ix_trips_school_id_scheduled", "school_id", "scheduled_start"),
    )


class TripLocation(Base):
    """GPS location record for a trip."""

    __tablename__ = "trip_locations"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    accuracy: Mapped[float | None] = mapped_column(Float)
    speed: Mapped[int | None] = mapped_column(Integer)
    heading: Mapped[int | None] = mapped_column(Integer)
    sequence_number: Mapped[int | None] = mapped_column(Integer)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    trip: Mapped["Trip"] = relationship("Trip", back_populates="location_updates")

    __table_args__ = (Index("ix_trip_locations_trip_id", "trip_id"), Index("ix_trip_locations_trip_recorded", "trip_id", "recorded_at"))


class Attendance(Base):
    """Student attendance/pickup/drop record."""

    __tablename__ = "attendances"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    trip_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    action: Mapped[str] = mapped_column(String(20), default="PENDING")
    idempotency_key: Mapped[str | None] = mapped_column(String(100), unique=True)
    action_taken_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    verified_by_driver: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (Index("ix_attendances_school_id", "school_id"), Index("ix_attendances_trip_id", "trip_id"),)