"""Initial database schema creation.

Creates all tables for the CouchSurfing application:
- users
- listings
- bookings
- reviews
- messages

Revision ID: initial_schema
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all database tables."""
    
    # Create enums first
    op.execute("""
        CREATE TYPE userrole AS ENUM ('guest', 'host', 'moderator')
    """)
    
    op.execute("""
        CREATE TYPE verificationstatus AS ENUM ('unverified', 'pending', 'verified', 'rejected')
    """)
    
    op.execute("""
        CREATE TYPE bookingstatus AS ENUM ('new', 'pending', 'confirmed', 'rejected', 'cancelled', 'completed')
    """)
    
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('guest', 'host', 'moderator', name='userrole'), nullable=False, server_default='guest'),
        sa.Column('verification_status', sa.Enum('unverified', 'pending', 'verified', 'rejected', name='verificationstatus'), nullable=False, server_default='unverified'),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    
    # Listings table
    op.create_table(
        'listings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('host_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('address', sa.String(length=500), nullable=False),
        sa.Column('capacity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('price_per_night', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('amenities', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['host_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_listings_host_id', 'listings', ['host_id'])
    op.create_index('ix_listings_city', 'listings', ['city'])
    op.create_index('ix_listings_city_active', 'listings', ['city', 'is_active'])
    op.create_index('ix_listings_host_active', 'listings', ['host_id', 'is_active'])
    
    # Bookings table
    op.create_table(
        'bookings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('guest_id', sa.Integer(), nullable=False),
        sa.Column('listing_id', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('status', sa.Enum('new', 'pending', 'confirmed', 'rejected', 'cancelled', 'completed', name='bookingstatus'), nullable=False, server_default='new'),
        sa.Column('guest_message', sa.Text(), nullable=True),
        sa.Column('host_response', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['guest_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['listing_id'], ['listings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_bookings_guest_id', 'bookings', ['guest_id'])
    op.create_index('ix_bookings_listing_id', 'bookings', ['listing_id'])
    op.create_index('ix_bookings_status', 'bookings', ['status'])
    op.create_index('ix_bookings_dates', 'bookings', ['start_date', 'end_date'])
    op.create_index('ix_bookings_listing_dates', 'bookings', ['listing_id', 'start_date', 'end_date'])
    
    # Reviews table
    op.create_table(
        'reviews',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('booking_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('target_id', sa.Integer(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('is_visible', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_reviews_booking_id', 'reviews', ['booking_id'])
    op.create_index('ix_reviews_author_id', 'reviews', ['author_id'])
    op.create_index('ix_reviews_target_id', 'reviews', ['target_id'])
    op.create_index('ix_reviews_target', 'reviews', ['target_id', 'is_visible'])
    op.create_index('ix_reviews_booking_unique', 'reviews', ['booking_id', 'author_id'], unique=True)
    
    # Messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=False),
        sa.Column('receiver_id', sa.Integer(), nullable=False),
        sa.Column('booking_id', sa.Integer(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['receiver_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_messages_sender_id', 'messages', ['sender_id'])
    op.create_index('ix_messages_receiver_id', 'messages', ['receiver_id'])
    op.create_index('ix_messages_booking_id', 'messages', ['booking_id'])
    op.create_index('ix_messages_conversation', 'messages', ['sender_id', 'receiver_id', 'created_at'])
    op.create_index('ix_messages_unread', 'messages', ['receiver_id', 'is_read'])


def downgrade() -> None:
    """Drop all database tables."""
    
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('messages')
    op.drop_table('reviews')
    op.drop_table('bookings')
    op.drop_table('listings')
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS bookingstatus')
    op.execute('DROP TYPE IF EXISTS verificationstatus')
    op.execute('DROP TYPE IF EXISTS userrole')
