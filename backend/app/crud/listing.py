"""
Listing CRUD Operations - Асинхронные операции с жильем
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional, Tuple
from datetime import date

from app.models import Listing, Booking, BookingStatus
from app.schemas.listing import ListingCreate, ListingUpdate, ListingSearchFilters


class ListingCRUD:
    """Класс для операций с жильем в БД"""
    
    async def create(
        self, 
        db: AsyncSession, 
        listing_data: ListingCreate, 
        host_id: int
    ) -> Listing:
        """Создание нового жилья"""
        import json
        
        # Преобразуем amenities из списка в JSON-строку для хранения в БД
        data_dict = listing_data.model_dump()
        if data_dict.get("amenities") is not None and isinstance(data_dict["amenities"], list):
            data_dict["amenities"] = json.dumps(data_dict["amenities"])
        
        listing = Listing(
            host_id=host_id,
            **data_dict
        )
        db.add(listing)
        await db.commit()
        await db.refresh(listing)
        return listing
    
    async def get_by_id(self, db: AsyncSession, listing_id: int) -> Optional[Listing]:
        """Получение жилья по ID"""
        result = await db.execute(
            select(Listing)
            .options(selectinload(Listing.images))
            .where(Listing.id == listing_id)
        )
        return result.scalar_one_or_none()
    
    async def get_host_listings(
        self, 
        db: AsyncSession, 
        host_id: int, 
        include_inactive: bool = False
    ) -> List[dict]:
        """Получение всех жилья конкретного хоста"""
        
        query = (
            select(Listing)
            .options(selectinload(Listing.images))
            .where(Listing.host_id == host_id)
        )
        
        if not include_inactive:
            query = query.where(Listing.is_active == True)
        
        result = await db.execute(query.order_by(Listing.created_at.desc()))
        listings = list(result.scalars().unique().all())
        
        # Преобразуем в словари с primary_image_url
        result_list = []
        for listing in listings:
            primary_image = None
            if listing.images:
                primary_img = next((img for img in listing.images if img.is_primary), None)
                if not primary_img and listing.images:
                    primary_img = listing.images[0]
                if primary_img:
                    primary_image = primary_img.image_url
            
            result_list.append({
                "id": listing.id,
                "title": listing.title,
                "city": listing.city,
                "capacity": listing.capacity,
                "is_active": listing.is_active,
                "primary_image_url": primary_image
            })
        
        return result_list
    
    async def update(
        self, 
        db: AsyncSession, 
        listing_id: int, 
        update_data: ListingUpdate
    ) -> Optional[Listing]:
        """Обновление жилья"""
        listing = await self.get_by_id(db, listing_id)
        if not listing:
            return None
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(listing, field, value)
        
        await db.commit()
        await db.refresh(listing)
        return listing
    
    async def delete(self, db: AsyncSession, listing_id: int) -> bool:
        """Удаление жилья (мягкое удаление через is_active=False)"""
        listing = await self.get_by_id(db, listing_id)
        if not listing:
            return False
        
        listing.is_active = False
        await db.commit()
        return True
    
    async def search(
        self,
        db: AsyncSession,
        filters: ListingSearchFilters
    ) -> Tuple[List[dict], int]:
        """
        Поиск жилья с фильтрацией по городу, датам и вместимости.
        Возвращает список жилья (как словари) и общее количество результатов.
        
        Логика проверки дат:
        - Бронирование конфликтует, если интервалы пересекаются
        - [start1, end1] пересекает [start2, end2] если start1 < end2 AND end1 > start2
        """
        from sqlalchemy.orm import selectinload
        
        # Базовый запрос
        base_query = (
            select(Listing)
            .options(selectinload(Listing.images))
            .where(Listing.is_active == True)
        )
        
        # Фильтр по городу (частичное совпадение, case-insensitive)
        if filters.city:
            base_query = base_query.where(
                func.lower(Listing.city).contains(func.lower(filters.city))
            )
        
        # Фильтр по вместимости
        if filters.min_capacity:
            base_query = base_query.where(Listing.capacity >= filters.min_capacity)
        
        # Фильтр по датам (исключение занятых listings)
        if filters.check_in and filters.check_out:
            # Подзапрос для поиска ID жилья с конфликтующими бронированиями
            busy_subquery = (
                select(Booking.listing_id)
                .where(
                    Booking.status.in_([
                        BookingStatus.CONFIRMED,
                        BookingStatus.PENDING,
                        BookingStatus.COMPLETED
                    ])
                )
                .where(
                    # Пересечение интервалов:
                    # existing_start < new_end AND existing_end > new_start
                    and_(
                        Booking.start_date < filters.check_out,
                        Booking.end_date > filters.check_in
                    )
                )
            )
            
            # Исключаем занятые listings
            base_query = base_query.where(
                ~Listing.id.in_(busy_subquery)
            )
        
        # Получаем общее количество для пагинации
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Применяем пагинацию
        base_query = base_query.offset(filters.offset).limit(filters.size)
        
        result = await db.execute(base_query.order_by(Listing.created_at.desc()))
        listings = list(result.scalars().unique().all())
        
        # Преобразуем в словари с primary_image_url
        result_list = []
        for listing in listings:
            primary_image = None
            if listing.images:
                primary_img = next((img for img in listing.images if img.is_primary), None)
                if not primary_img and listing.images:
                    primary_img = listing.images[0]
                if primary_img:
                    primary_image = primary_img.image_url
            
            result_list.append({
                "id": listing.id,
                "title": listing.title,
                "city": listing.city,
                "capacity": listing.capacity,
                "is_active": listing.is_active,
                "primary_image_url": primary_image
            })
        
        return result_list, total
    
    async def check_availability(
        self,
        db: AsyncSession,
        listing_id: int,
        start_date: date,
        end_date: date
    ) -> bool:
        """
        Проверка доступности жилья на указанные даты.
        Возвращает True, если жилье свободно.
        """
        # Ищем конфликтующие бронирования
        conflict = await db.execute(
            select(Booking)
            .where(Booking.listing_id == listing_id)
            .where(
                Booking.status.in_([
                    BookingStatus.CONFIRMED,
                    BookingStatus.PENDING
                ])
            )
            .where(
                and_(
                    Booking.start_date < end_date,
                    Booking.end_date > start_date
                )
            )
        )
        
        return conflict.scalar_one_or_none() is None


# Экземпляр для использования в роутерах
listing_crud = ListingCRUD()
