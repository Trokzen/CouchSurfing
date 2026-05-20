"""
Schemas __init__ - Экспорт всех схем
"""
from app.schemas.auth import (
    UserRole,
    VerificationStatus,
    UserRegister,
    UserLogin,
    Token,
    TokenPayload,
    UserResponse,
    UserUpdate,
    PasswordChange,
)

from app.schemas.common import (
    BaseResponse,
    ErrorResponse,
    PaginationParams,
    PaginatedResponse,
)

from app.schemas.listing import (
    ListingCreate,
    ListingUpdate,
    ListingResponse,
    ListingBrief,
    ListingSearchFilters,
)

from app.schemas.booking import (
    BookingStatus,
    BookingCreate,
    BookingUpdate,
    BookingResponse,
    BookingWithDetailsResponse,
    BookingBrief,
    BookingStatusChange,
    AvailabilityCheck,
    AvailabilityResponse,
)

from app.schemas.review import (
    ReviewCreate,
    ReviewResponse,
    ReviewBrief,
    UserRatingSummary,
)

from app.schemas.message import (
    MessageCreate,
    MessageResponse,
    MessageBrief,
    ConversationPreview,
)

__all__ = [
    # Auth
    "UserRole",
    "VerificationStatus",
    "UserRegister",
    "UserLogin",
    "Token",
    "TokenPayload",
    "UserResponse",
    "UserUpdate",
    "PasswordChange",
    # Common
    "BaseResponse",
    "ErrorResponse",
    "PaginationParams",
    "PaginatedResponse",
    # Listing
    "ListingCreate",
    "ListingUpdate",
    "ListingResponse",
    "ListingBrief",
    "ListingSearchFilters",
    # Booking
    "BookingStatus",
    "BookingCreate",
    "BookingUpdate",
    "BookingResponse",
    "BookingWithDetailsResponse",
    "BookingBrief",
    "BookingStatusChange",
    "AvailabilityCheck",
    "AvailabilityResponse",
    # Review
    "ReviewCreate",
    "ReviewResponse",
    "ReviewBrief",
    "UserRatingSummary",
    # Message
    "MessageCreate",
    "MessageResponse",
    "MessageBrief",
    "ConversationPreview",
]
