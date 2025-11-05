"""
Custom exceptions for the application.
"""


class AppException(Exception):
    """Base application exception."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR", status_code: int = 500):
        """Initialize exception."""
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(AppException):
    """Validation error."""

    def __init__(self, message: str, code: str = "VALIDATION_ERROR"):
        super().__init__(message, code, 400)


class AuthenticationError(AppException):
    """Authentication error."""

    def __init__(self, message: str = "Invalid credentials", code: str = "AUTHENTICATION_ERROR"):
        super().__init__(message, code, 401)


class AuthorizationError(AppException):
    """Authorization error."""

    def __init__(self, message: str = "Insufficient permissions", code: str = "AUTHORIZATION_ERROR"):
        super().__init__(message, code, 403)


class NotFoundError(AppException):
    """Resource not found error."""

    def __init__(self, resource: str = "Resource", code: str = "NOT_FOUND"):
        message = f"{resource} not found"
        super().__init__(message, code, 404)


class ConflictError(AppException):
    """Conflict error (e.g., duplicate resource)."""

    def __init__(self, message: str, code: str = "CONFLICT"):
        super().__init__(message, code, 409)


class RateLimitError(AppException):
    """Rate limit exceeded."""

    def __init__(self, message: str = "Too many requests", code: str = "RATE_LIMIT_EXCEEDED"):
        super().__init__(message, code, 429)


class DatabaseError(AppException):
    """Database error."""

    def __init__(self, message: str, code: str = "DATABASE_ERROR"):
        super().__init__(message, code, 500)


class ExternalServiceError(AppException):
    """External service error."""

    def __init__(
        self, service: str = "External service", message: str = "Service unavailable", code: str = "SERVICE_ERROR"
    ):
        msg = f"{service}: {message}"
        super().__init__(msg, code, 503)


class OdooIntegrationError(ExternalServiceError):
    """Odoo integration error."""

    def __init__(self, message: str, code: str = "ODOO_ERROR"):
        super().__init__("Odoo", message, code)


class DetectionProviderError(ExternalServiceError):
    """Detection provider error."""

    def __init__(self, message: str, code: str = "DETECTION_ERROR"):
        super().__init__("Detection Provider", message, code)


class CameraError(AppException):
    """Camera error."""

    def __init__(self, message: str, code: str = "CAMERA_ERROR"):
        super().__init__(message, code, 400)


class FileUploadError(AppException):
    """File upload error."""

    def __init__(self, message: str, code: str = "FILE_UPLOAD_ERROR"):
        super().__init__(message, code, 400)


class ExportError(AppException):
    """Export generation error."""

    def __init__(self, message: str, code: str = "EXPORT_ERROR"):
        super().__init__(message, code, 500)
