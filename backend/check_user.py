import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import select
from app.models import User

async def check_user():
    DATABASE_URL = "postgresql+asyncpg://postgres:1234@localhost:5432/postgres?options=-c%20search_path%3Dcouchsurfing"
    engine = create_async_engine(DATABASE_URL, echo=True)
    async with engine.connect() as conn:
        result = await conn.execute(select(User).where(User.email == "testuser@example.com"))
        user = result.scalar_one_or_none()
        if user:
            print(f"User found: {user.id}, {user.email}, {user.full_name}")
        else:
            print("User not found")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_user())