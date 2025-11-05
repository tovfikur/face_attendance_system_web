"""
API v1 router that includes all endpoints.
"""

from fastapi import APIRouter

from app.api.v1.attendance import router as attendance_router
from app.api.v1.attendance_ws import router as attendance_ws_router
from app.api.v1.auth import router as auth_router
from app.api.v1.cameras import router as cameras_router
from app.api.v1.detections import router as detections_router
from app.api.v1.persons import router as persons_router
from app.api.v1.roles import router as roles_router
from app.api.v1.users import router as users_router

api_router = APIRouter()

# Include all routers
api_router.include_router(auth_router)
api_router.include_router(roles_router)
api_router.include_router(users_router)
api_router.include_router(cameras_router, prefix="/cameras")
api_router.include_router(detections_router, prefix="/detections")
api_router.include_router(persons_router, prefix="/persons")
api_router.include_router(attendance_router, prefix="/attendance")
api_router.include_router(attendance_ws_router, prefix="/attendance")

# TODO: Include additional routers as they are implemented
# api_router.include_router(cameras_router)
# api_router.include_router(detections_router)
# api_router.include_router(attendance_router)
# api_router.include_router(faces_router)
# api_router.include_router(alerts_router)
# api_router.include_router(odoo_router)
# api_router.include_router(users_router)
# api_router.include_router(system_router)
# api_router.include_router(audit_router)
# api_router.include_router(settings_router)
# api_router.include_router(developer_router)
# api_router.include_router(history_router)
