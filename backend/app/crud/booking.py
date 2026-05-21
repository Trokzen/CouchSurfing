"""
Booking CRUD Operations - Асинхронные операции с бронированиями
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional, Tuple
from datetime import date

from app.models import Booking, Listing, BookingStatus, User
from app.schemas.booking import BookingCreate, BookingStatusChange


class BookingCRUD:
    """Класс для операций с бронированиями в БД"""
    
    async def create(
        self, 
        db: AsyncSession, 
        booking_data: BookingCreate, 
        guest_id: int
    ) -> Booking:
        """Создание нового бронирования со статусом 'new'"""
        booking = Booking(
            guest_id=guest_id,
            listing_id=booking_data.listing_id,
            start_date=booking_data.start_date,
            end_date=booking_data.end_date,
            guest_message=booking_data.message,
            status=BookingStatus.NEW
        )
        db.add(booking)
        await db.commit()
        await db.refresh(booking)
        return booking
    
    async def get_by_id(self, db: AsyncSession, booking_id: int) -> Optional[Booking]:
        """Получение бронирования по ID с загрузкой связанных данных"""
        result = await db.execute(
            select(Booking)
            .options(selectinload(Booking.listing), selectinload(Booking.guest))
            .where(Booking.id == booking_id)
        )
        return result.scalar_one_or_none()
    
    async def get_guest_bookings(
        self, 
        db: AsyncSession, 
        guest_id: int,
        status: Optional[BookingStatus] = None
    ) -> List[Booking]:
        """Получение всех бронирований гостя"""
        query = select(Booking).where(Booking.guest_id == guest_id)
        
        if status:
            query = query.where(Booking.status == status)
        
        query = query.options(selectinload(Booking.listing))
        query = query.order_by(Booking.created_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_host_bookings(
        self, 
        db: AsyncSession, 
        host_id: int,
        status: Optional[BookingStatus] = None
    ) -> List[Booking]:
        """Получение всех бронирований жилья конкретного хоста"""
        query = (
            select(Booking)
            .join(Listing)
            .where(Listing.host_id == host_id)
            .options(selectinload(Booking.guest))
        )
        
        if status:
            query = query.where(Booking.status == status)
        
        query = query.order_by(Booking.created_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def update_status(
        self, 
        db: AsyncSession, 
        booking_id: int, 
        new_status: BookingStatus
    ) -> Optional[Booking]:
        """Обновление статуса бронирования"""
        booking = await self.get_by_id(db, booking_id)
        if not booking:
            return None
        
        booking.status = new_status
        await db.commit()
        await db.refresh(booking)
        return booking
    
    async def check_date_conflict(
        self,
        db: AsyncSession,
        listing_id: int,
        start_date: date,
        end_date: date,
        exclude_booking_id: Optional[int] = None
    ) -> List[Booking]:
        """
        Проверка пересечения дат с существующими бронированиями.
        Возвращает список конфликтующих бронирований.
        
        Логика: интервалы [start1, end1] и [start2, end2] пересекаются,
        если start1 < end2 AND end1 > start2
        """
        query = (
            select(Booking)
            .where(Booking.listing_id == listing_id)
            .where(
                Booking.status.in_([
                    BookingStatus.CONFIRMED,
                    BookingStatus.PENDING,
                    BookingStatus.NEW
                ])
            )
            .where(
                and_(
                    Booking.start_date < end_date,
                    Booking.end_date > start_date
                )
            )
        )
        
        if exclude_booking_id:
            query = query.where(Booking.id != exclude_booking_id)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_completed_bookings_for_review(
        self,
        db: AsyncSession,
        user_id: int
    ) -> List[Booking]:
        """
        Получение завершенных бронирований, для которых еще нет отзыва.
        user_id может быть либо guest_id, либо target_id (хостом).
        """
        # Бронирования где пользователь был гостем
        query_guest = (
            select(Booking)
            .where(Booking.guest_id == user_id)
            .where(Booking.status == BookingStatus.COMPLETED)
            .options(selectinload(Booking.listing))
        )
        
        result = await db.execute(query_guest)
        return list(result.scalars().all())


# Экземпляр для использования в роутерах
booking_crud = BookingCRUD()
