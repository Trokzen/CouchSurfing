import asyncio
import sys
import os
from datetime import date, timedelta, datetime

# Добавляем путь к приложению
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal, engine
from app.models import User, Listing, Booking, BookingStatus, UserRole, VerificationStatus
from app.services.auth import AuthService

async def seed_data():
    print("Starting database seeding...")
    async with AsyncSessionLocal() as db:
        # 1. Проверяем наличие аккаунтов из сообщения
        # host@ya.ru (ID 5)
        # test@ya.ru (ID 4)
        
        from sqlalchemy import select
        
        # Получаем хоста
        result = await db.execute(select(User).where(User.email == "host@ya.ru"))
        host = result.scalar_one_or_none()
        
        if not host:
            print("Host user host@ya.ru not found. Please register it first.")
            return

        # Получаем гостя
        result = await db.execute(select(User).where(User.email == "test@ya.ru"))
        guest = result.scalar_one_or_none()
        
        if not guest:
            print("Guest user test@ya.ru not found. Please register it first.")
            return

        # 2. Создаем жилье (Listings)
        listings_data = [
            {
                "title": "Уютная студия в центре Москвы",
                "description": "Прекрасная студия с видом на город. Есть всё необходимое для комфортного проживания: Wi-Fi, кухня, стиральная машина.",
                "city": "Москва",
                "address": "ул. Тверская, д. 10",
                "capacity": 2,
                "amenities": "Wi-Fi, Кухня, Стиральная машина, Кондиционер",
                "is_active": True
            },
            {
                "title": "Просторная квартира рядом с парком",
                "description": "Тихое место, идеально для отдыха. Большая кровать, балкон, рядом много кафе и магазинов.",
                "city": "Санкт-Петербург",
                "address": "Невский проспект, д. 15",
                "capacity": 3,
                "amenities": "Wi-Fi, Балкон, Кофемашина, Фен",
                "is_active": True
            },
            {
                "title": "Домик у озера",
                "description": "Для любителей природы. Чистый воздух, рыбалка, мангал. Доступно только в летний сезон.",
                "city": "Казань",
                "address": "Дачный поселок Светлый, уч. 45",
                "capacity": 4,
                "amenities": "Мангал, Озеро, Парковка",
                "is_active": True
            }
        ]

        listings = []
        for l_data in listings_data:
            # Проверяем, нет ли уже такого жилья
            res = await db.execute(select(Listing).where(Listing.title == l_data["title"]))
            if not res.scalar_one_or_none():
                listing = Listing(
                    host_id=host.id,
                    **l_data
                )
                db.add(listing)
                listings.append(listing)
                print(f"Added listing: {l_data['title']}")
        
        await db.commit()

        # 3. Создаем бронирования (Bookings)
        # Перезагрузим листинги, чтобы получить их ID
        result = await db.execute(select(Listing).where(Listing.host_id == host.id))
        all_listings = result.scalars().all()
        
        if all_listings:
            today = date.today()
            
            bookings_data = [
                {
                    "listing_id": all_listings[0].id,
                    "guest_id": guest.id,
                    "start_date": today + timedelta(days=5),
                    "end_date": today + timedelta(days=10),
                    "status": BookingStatus.PENDING,
                    "guest_message": "Здравствуйте! Хотел бы пожить у вас неделю."
                },
                {
                    "listing_id": all_listings[1].id,
                    "guest_id": guest.id,
                    "start_date": today - timedelta(days=15),
                    "end_date": today - timedelta(days=10),
                    "status": BookingStatus.COMPLETED,
                    "guest_message": "Еду в командировку."
                },
                {
                    "listing_id": all_listings[0].id,
                    "guest_id": guest.id,
                    "start_date": today + timedelta(days=20),
                    "end_date": today + timedelta(days=25),
                    "status": BookingStatus.CONFIRMED,
                    "guest_message": "Спасибо за подтверждение!"
                }
            ]

            for b_data in bookings_data:
                # Простая проверка на дубликаты по датам и листингу
                res = await db.execute(
                    select(Booking).where(
                        Booking.listing_id == b_data["listing_id"],
                        Booking.start_date == b_data["start_date"]
                    )
                )
                if not res.scalar_one_or_none():
                    booking = Booking(**b_data)
                    db.add(booking)
                    print(f"Added booking for listing ID {b_data['listing_id']} with status {b_data['status']}")
            
            await db.commit()

    print("Seeding completed successfully!")

if __name__ == "__main__":
    asyncio.run(seed_data())
