"""API v1 endpoints package."""

from app.api.v1.endpoints.auth import auth_router
from app.api.v1.endpoints.schools import schools_router
from app.api.v1.endpoints.students import students_router
from app.api.v1.endpoints.vehicles import vehicles_router
from app.api.v1.endpoints.drivers import drivers_router
from app.api.v1.endpoints.routes import routes_router, trips_router, attendance_router

__all__ = [
    "auth_router",
    "schools_router",
    "students_router",
    "vehicles_router",
    "drivers_router",
    "routes_router",
    "trips_router",
    "attendance_router",
]