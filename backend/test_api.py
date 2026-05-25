import asyncio
import sys
sys.path.insert(0, '.')

from httpx import AsyncClient, ASGITransport
from app.main import app

async def test():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Test 1: search listings
        r = await client.get("/api/v1/listings/search?page=1&size=20")
        print(f"SEARCH: {r.status_code}")
        if r.status_code != 200:
            print(f"  ERROR: {r.text[:500]}")
        else:
            data = r.json()
            print(f"  OK: total={data['total']}, items={len(data['items'])}")

        # Test 2: login (form data for OAuth2PasswordRequestForm)
        r2 = await client.post("/api/v1/auth/login", data={
            "username": "test@ya.ru",
            "password": "password123",
        })
        print(f"LOGIN: {r2.status_code}")
        if r2.status_code != 200:
            print(f"  ERROR: {r2.text[:300]}")
            return

        token = r2.json().get("access_token", "")
        headers = {"Authorization": f"Bearer {token}"}

        # Test 3: bookings/my
        r3 = await client.get("/api/v1/bookings/my", headers=headers)
        print(f"BOOKINGS: {r3.status_code}")
        if r3.status_code != 200:
            print(f"  ERROR: {r3.text[:500]}")
        else:
            print(f"  OK: {r3.text[:300]}")

        # Test 4: host listings (as guest user 4 asking for host_id=5)
        r4 = await client.get("/api/v1/listings/?host_id=5&include_inactive=true", headers=headers)
        print(f"HOST LISTINGS: {r4.status_code}")
        if r4.status_code != 200:
            print(f"  ERROR: {r4.text[:500]}")
        else:
            print(f"  OK: {r4.text[:300]}")

asyncio.run(test())