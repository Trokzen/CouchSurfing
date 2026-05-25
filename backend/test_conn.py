import asyncio
import asyncpg

async def test():
    conn = await asyncpg.connect(
        host='localhost', port=5432, user='postgres',
        password='1234', database='postgres', timeout=5
    )
    
    # Check enum values
    rows = await conn.fetch("""
        SELECT e.enumlabel, t.typname
        FROM pg_enum e
        JOIN pg_type t ON e.enumtypid = t.oid
        JOIN pg_namespace n ON t.typnamespace = n.oid
        WHERE n.nspname = 'couchsurfing'
    """)
    print(f'Enum values: {[(r["typname"], r["enumlabel"]) for r in rows]}')
    
    await conn.close()

if __name__ == '__main__':
    asyncio.run(test())
