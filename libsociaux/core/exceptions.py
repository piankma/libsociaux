class PermissionDenied(Exception):
    """Raised when a user tries to make action that he is not allowed to."""

    pass


class InvalidCredentials(Exception):
    """Raised when the credentials are invalid."""

    pass


class InvalidResponse(Exception):
    """Raised when the response is invalid."""

    pass


class InvalidRequest(Exception):
    """Raised when the request is invalid."""

    pass


class QuotaExceeded(Exception):
    """Raised when the quota is exceeded."""

    pass


class NotFound(Exception):
    """Raised when the requested resource is not found."""

    pass


class ServiceError(Exception):
    """Raised when the service returns an unknown error."""

    pass
