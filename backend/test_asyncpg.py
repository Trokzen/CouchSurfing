import asyncio
import asyncpg

async def test():
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='1234',
            database='postgres',
            timeout=10
        )
        print("Asyncpg connected successfully")
        version = await conn.fetchval('SELECT version()')
        print(f"PostgreSQL version: {version}")
        await conn.close()
    except Exception as e:
        print(f"Asyncpg connection error: {e}")

asyncio.run(test())