"""Database models for CouchSurfing application."""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, List

from sqlalchemy import (
    String,
    Text,
    Integer,
    DateTime,
    Boolean,
    ForeignKey,
    Enum,
    Numeric,
    Index,
    func,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
    validates,
)

from app.core.database import Base


# ==================== ENUMS ====================


class UserRole(str, PyEnum):
    """User role enumeration."""

    GUEST = "guest"
    HOST = "host"
    MODERATOR = "moderator"


class VerificationStatus(str, PyEnum):
    """User verification status."""

    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class BookingStatus(str, PyEnum):
    """
    Booking status enumeration - State Machine.
    
    Lifecycle:
    1. new -> pending (when guest submits booking request)
    2. pending -> confirmed (host accepts)
    3. pending -> rejected (host declines)
    4. confirmed -> cancelled (guest cancels before check-in)
    5. confirmed -> completed (after checkout date passes)
    """

    NEW = "new"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


# ==================== MODELS ====================


class User(Base):
    """
    User model representing all system users.
    
    Roles: guest, host, moderator
    A user can be both guest and host simultaneously.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", values_callable=lambda x: [e.value for e in x]), default=UserRole.GUEST, nullable=False
    )
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, name="verification_status", values_callable=lambda x: [e.value for e in x]), default=VerificationStatus.UNVERIFIED, nullable=False
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    listings: Mapped[List["Listing"]] = relationship(
        "Listing", back_populates="host", cascade="all, delete-orphan"
    )
    bookings_as_guest: Mapped[List["Booking"]] = relationship(
        "Booking", back_populates="guest", foreign_keys="Booking.guest_id"
    )
    reviews_authored: Mapped[List["Review"]] = relationship(
        "Review", back_populates="author", foreign_keys="Review.author_id"
    )
    reviews_received: Mapped[List["Review"]] = relationship(
        "Review", back_populates="target", foreign_keys="Review.target_id"
    )
    sent_messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="sender", foreign_keys="Message.sender_id"
    )
    received_messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="receiver", foreign_keys="Message.receiver_id"
    )

    @validates("email")
    def validate_email(self, key: str, value: str) -> str:
        """Validate email format."""
        if "@" not in value or "." not in value:
            raise ValueError("Invalid email format")
        return value.lower()

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


class Listing(Base):
    """
    Listing model representing accommodation offered by hosts.
    """

    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    host_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    price_per_night: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    amenities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    host: Mapped["User"] = relationship("User", back_populates="listings")
    bookings: Mapped[List["Booking"]] = relationship(
        "Booking", back_populates="listing", cascade="all, delete-orphan"
    )
    images: Mapped[List["ListingImage"]] = relationship(
        "ListingImage", back_populates="listing", cascade="all, delete-orphan"
    )

    # Indexes for efficient searching
    __table_args__ = (
        Index("ix_listings_city_active", "city", "is_active"),
        Index("ix_listings_host_active", "host_id", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Listing(id={self.id}, title={self.title}, city={self.city})>"


class ListingImage(Base):
    """
    ListingImage model representing photos of a listing.
    """

    __tablename__ = "listing_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(
        ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    listing: Mapped["Listing"] = relationship("Listing", back_populates="images")

    __table_args__ = (
        Index("ix_listing_images_listing", "listing_id", "is_primary"),
    )

    def __repr__(self) -> str:
        return f"<ListingImage(id={self.id}, listing_id={self.listing_id}, primary={self.is_primary})>"


class Booking(Base):
    """
    Booking model representing a reservation request.
    
    State Machine:
    - Guest creates booking -> status: NEW
    - System processes -> status: PENDING (waiting for host)
    - Host accepts -> status: CONFIRMED
    - Host rejects -> status: REJECTED
    - Guest cancels -> status: CANCELLED
    - After checkout -> status: COMPLETED
    """

    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guest_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    listing_id: Mapped[int] = mapped_column(
        ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, name="booking_status", values_callable=lambda x: [e.value for e in x]), default=BookingStatus.NEW, nullable=False, index=True
    )
    guest_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    host_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    guest: Mapped["User"] = relationship(
        "User", back_populates="bookings_as_guest", foreign_keys=[guest_id]
    )
    listing: Mapped["Listing"] = relationship("Listing", back_populates="bookings")
    reviews: Mapped[List["Review"]] = relationship(
        "Review", back_populates="booking", cascade="all, delete-orphan"
    )
    messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="booking", cascade="all, delete-orphan"
    )

    # Indexes for date range queries
    __table_args__ = (
        Index("ix_bookings_dates", "start_date", "end_date"),
        Index("ix_bookings_listing_dates", "listing_id", "start_date", "end_date"),
    )

    @validates("start_date", "end_date")
    def validate_dates(self, key: str, value: datetime) -> datetime:
        """Validate that end_date is after start_date."""
        if key == "end_date" and hasattr(self, "start_date"):
            if value <= self.start_date:
                raise ValueError("End date must be after start date")
        return value

    def __repr__(self) -> str:
        return f"<Booking(id={self.id}, status={self.status}, dates={self.start_date} to {self.end_date})>"


class Review(Base):
    """
    Review model for ratings and comments.
    
    Can only be created after booking status is COMPLETED.
    Both guest and host can review each other.
    """

    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    booking_id: Mapped[int] = mapped_column(
        ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    booking: Mapped["Booking"] = relationship("Booking", back_populates="reviews")
    author: Mapped["User"] = relationship(
        "User", back_populates="reviews_authored", foreign_keys=[author_id]
    )
    target: Mapped["User"] = relationship(
        "User", back_populates="reviews_received", foreign_keys=[target_id]
    )

    # Constraints
    __table_args__ = (
        # Ensure rating is between 1 and 5
        # Note: Check constraints need to be added via Alembic
        Index("ix_reviews_target", "target_id", "is_visible"),
        Index("ix_reviews_booking_unique", "booking_id", "author_id", unique=True),
    )

    @validates("rating")
    def validate_rating(self, key: str, value: int) -> int:
        """Validate rating is between 1 and 5."""
        if not 1 <= value <= 5:
            raise ValueError("Rating must be between 1 and 5")
        return value

    def __repr__(self) -> str:
        return f"<Review(id={self.id}, rating={self.rating}, author={self.author_id})>"


class Message(Base):
    """
    Message model for communication between users.
    
    Messages can be associated with a booking or be general.
    """

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    receiver_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    booking_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    sender: Mapped["User"] = relationship(
        "User", back_populates="sent_messages", foreign_keys=[sender_id]
    )
    receiver: Mapped["User"] = relationship(
        "User", back_populates="received_messages", foreign_keys=[receiver_id]
    )
    booking: Mapped[Optional["Booking"]] = relationship(
        "Booking", back_populates="messages"
    )

    # Indexes for efficient message retrieval
    __table_args__ = (
        Index("ix_messages_conversation", "sender_id", "receiver_id", "created_at"),
        Index("ix_messages_unread", "receiver_id", "is_read"),
    )

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, from={self.sender_id}, to={self.receiver_id})>"
