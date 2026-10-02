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
    Column,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    func,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from geoalchemy2 import Geography

from app.infrastructure.database import Base
from app.core.security import Role, AttendanceStatus, TripStatus, Permission


# Association table for user-school membership (many-to-many)
school_memberships = Table(
    "school_memberships",
    Base.metadata,
    Column("id", PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("school_id", PGUUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
    Column("user_id", PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("role", SAEnum(Role), nullable=False),
    Column("joined_at", DateTime(timezone=True), server_default=func.now()),
    Column("left_at", DateTime(timezone=True), nullable=True),
    Column("is_active", Boolean, default=True),
    UniqueConstraint("school_id", "user_id", name="uq_school_user"),
    Index("ix_school_memberships_school_id", "school_id"),
    Index("ix_school_memberships_user_id", "user_id"),
)