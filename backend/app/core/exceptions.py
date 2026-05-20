"""Custom exception classes for the application."""

from typing import Any, Optional


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str = "An error occurred",
        status_code: int = 500,
        detail: Optional[Any] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)


class ValidationException(AppException):
    """Raised when validation fails."""

    def __init__(self, message: str = "Validation error", detail: Optional[Any] = None):
        super().__init__(message=message, status_code=400, detail=detail)


class NotFoundException(AppException):
    """Raised when a resource is not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message=message, status_code=404)


class AuthenticationException(AppException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message=message, status_code=401)


class AuthorizationException(AppException):
    """Raised when authorization fails."""

    def __init__(self, message: str = "Access denied"):
        super().__init__(message=message, status_code=403)


class ConflictException(AppException):
    """Raised when there's a conflict (e.g., duplicate resource)."""

    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message=message, status_code=409)


# Специфичные исключения для Auth модуля

class EmailAlreadyExistsError(ConflictException):
    """Raised when trying to register with an existing email."""

    def __init__(self, email: str):
        super().__init__(message=f"Email '{email}' is already registered")


class UserNotFoundError(NotFoundException):
    """Raised when user is not found."""

    def __init__(self, user_id: Optional[int] = None):
        if user_id:
            super().__init__(message=f"User with ID {user_id} not found")
        else:
            super().__init__(message="User not found")


class InvalidCredentialsError(AuthenticationException):
    """Raised when login credentials are invalid."""

    def __init__(self):
        super().__init__(message="Invalid email or password")


class TokenExpiredError(AuthenticationException):
    """Raised when JWT token has expired."""

    def __init__(self):
        super().__init__(message="Token has expired")


class InvalidTokenError(AuthenticationException):
    """Raised when JWT token is invalid."""

    def __init__(self):
        super().__init__(message="Invalid token")
