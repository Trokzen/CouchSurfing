"""Database connection and session management."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    async_scoped_session,
)
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy.pool import NullPool
import asyncio

from app.core.config import get_settings

settings = get_settings()


class Base(DeclarativeBase):
    """Base class for all database models."""

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Generate table name from class name (lowercase + 's')."""
        return f"{cls.__name__.lower()}s"


# Create async engine with proper settings for development
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    poolclass=NullPool,  # Use NullPool for better async compatibility in dev
    future=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Scoped session for request-level isolation
# Uses asyncio.get_running_loop() to ensure session is tied to current async task
db_session = async_scoped_session(
    session_factory=AsyncSessionLocal,
    scopefunc=asyncio.current_task,
)


async def get_db() -> AsyncSession:
    """
    Dependency that provides a database session.
    
    Usage in FastAPI routes:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with db_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables (for development only)."""
    async with engine.begin() as conn:
        # Import all models to ensure they are registered with Base
        from app.models import User, Listing, Booking, Review, Message
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
