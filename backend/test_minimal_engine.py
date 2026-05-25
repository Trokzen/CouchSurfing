import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def test():
    # Use the same connection string as in config
    DATABASE_URL = "postgresql+asyncpg://postgres:1234@localhost:5432/postgres"
    engine = create_async_engine(
        DATABASE_URL,
        echo=True,
        poolclass=None,  # default pool
        future=True,
    )
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print(f"Connection successful: {result.scalar()}")
            result = await conn.execute(text("SELECT current_schema()"))
            print(f"Current schema: {result.scalar()}")
    except Exception as e:
        print(f"Connection failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test())