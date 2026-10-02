"""API v1 router configuration."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth_router,
    schools_router,
    students_router,
    vehicles_router,
    drivers_router,
    routes_router,
    trips_router,
    attendance_router,
)

# Main API router
api_router = APIRouter(prefix="/api/v1", tags=["API"])

# Include all module routers
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(schools_router, prefix="/schools", tags=["Schools"])
api_router.include_router(students_router, prefix="/students", tags=["Students"])
api_router.include_router(vehicles_router, prefix="/vehicles", tags=["Vehicles"])
api_router.include_router(drivers_router, prefix="/drivers", tags=["Drivers"])
api_router.include_router(routes_router, prefix="/routes", tags=["Routes"])
api_router.include_router(trips_router, prefix="/trips", tags=["Trips"])
api_router.include_router(attendance_router, prefix="/attendance", tags=["Attendance"])