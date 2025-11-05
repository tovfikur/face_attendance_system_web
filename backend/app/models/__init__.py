"""SQLAlchemy models."""

from app.models.attendance import (
    Attendance,
    AttendanceException,
    AttendanceRule,
    AttendanceSession,
)
from app.models.camera import (
    Camera,
    CameraGroup,
    CameraHealth,
    CameraSnapshot,
)
from app.models.detection import (
    Detection,
    DetectionEventLog,
    DetectionProcessingQueue,
    DetectionProviderConfig,
)
from app.models.person import (
    Person,
    PersonFaceEncoding,
    PersonImage,
    PersonMetadata,
)
from app.models.user import (
    Role,
    User,
    UserPreferences,
    UserSession,
)

__all__ = [
    # User models
    "User",
    "Role",
    "UserSession",
    "UserPreferences",
    # Camera models
    "Camera",
    "CameraGroup",
    "CameraHealth",
    "CameraSnapshot",
    # Detection models
    "Detection",
    "DetectionEventLog",
    "DetectionProcessingQueue",
    "DetectionProviderConfig",
    # Person models
    "Person",
    "PersonFaceEncoding",
    "PersonImage",
    "PersonMetadata",
    # Attendance models
    "Attendance",
    "AttendanceSession",
    "AttendanceRule",
    "AttendanceException",
]
