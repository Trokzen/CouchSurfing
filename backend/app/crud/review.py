"""
Review CRUD Operations - Асинхронные операции с отзывами
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional, Tuple
from datetime import date

from app.models import Review, Booking, User, BookingStatus
from app.schemas.review import ReviewCreate


class ReviewCRUD:
    """Класс для операций с отзывами в БД"""
    
    async def create(
        self, 
        db: AsyncSession, 
        review_data: ReviewCreate, 
        author_id: int
    ) -> Review:
        """Создание нового отзыва"""
        review = Review(
            booking_id=review_data.booking_id,
            author_id=author_id,
            target_id=review_data.target_id,
            rating=review_data.rating,
            comment=review_data.comment
        )
        db.add(review)
        await db.commit()
        await db.refresh(review)
        return review
    
    async def get_by_id(self, db: AsyncSession, review_id: int) -> Optional[Review]:
        """Получение отзыва по ID с загрузкой связанных данных"""
        result = await db.execute(
            select(Review)
            .options(selectinload(Review.author), selectinload(Review.target))
            .where(Review.id == review_id)
        )
        return result.scalar_one_or_none()
    
    async def get_reviews_for_user(
        self, 
        db: AsyncSession, 
        user_id: int,
        limit: int = 10
    ) -> List[Review]:
        """Получение отзывов для конкретного пользователя (как target)"""
        query = (
            select(Review)
            .where(Review.target_id == user_id)
            .where(Review.is_visible == True)
            .options(selectinload(Review.author))
            .order_by(Review.created_at.desc())
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_user_rating_summary(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> Tuple[float, int, dict]:
        """
        Получение сводной информации о рейтинге пользователя.
        Возвращает: (average_rating, total_reviews, rating_distribution)
        """
        # Получаем все видимые отзывы для пользователя
        query = select(Review).where(
            Review.target_id == user_id,
            Review.is_visible == True
        )
        result = await db.execute(query)
        reviews = list(result.scalars().all())
        
        if not reviews:
            return 0.0, 0, {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        
        total_reviews = len(reviews)
        total_rating = sum(r.rating for r in reviews)
        average_rating = total_rating / total_reviews
        
        # Распределение по рейтингам
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for review in reviews:
            distribution[review.rating] += 1
        
        return average_rating, total_reviews, distribution
    
    async def has_reviewed(
        self, 
        db: AsyncSession, 
        booking_id: int, 
        author_id: int
    ) -> bool:
        """Проверка, оставлял ли пользователь отзыв для данного бронирования"""
        query = select(Review).where(
            Review.booking_id == booking_id,
            Review.author_id == author_id
        )
        result = await db.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def can_review_booking(
        self, 
        db: AsyncSession, 
        booking_id: int, 
        user_id: int
    ) -> Tuple[bool, str]:
        """
        Проверка может ли пользователь оставить отзыв для бронирования.
        Возвращает: (can_review, reason)
        """
        # Загружаем бронирование
        result = await db.execute(
            select(Booking)
            .options(selectinload(Booking.guest), selectinload(Booking.listing))
            .where(Booking.id == booking_id)
        )
        booking = result.scalar_one_or_none()
        
        if not booking:
            return False, "Бронирование не найдено"
        
        # Проверяем что пользователь участвовал в бронировании
        is_guest = (booking.guest_id == user_id)
        is_host = False
        if booking.listing:
            is_host = (booking.listing.host_id == user_id)
        
        if not is_guest and not is_host:
            return False, "Вы не участвовали в этом бронировании"
        
        # Проверяем статус бронирования - должен быть completed
        if booking.status != BookingStatus.COMPLETED:
            return False, f"Нельзя оставить отзыв для бронирования со статусом '{booking.status.value}'. Статус должен быть 'completed'."
        
        # Проверяем не оставлял ли уже отзыв
        already_reviewed = await self.has_reviewed(db, booking_id, user_id)
        if already_reviewed:
            return False, "Вы уже оставили отзыв для этого бронирования"
        
        return True, ""
    
    async def update_visibility(
        self, 
        db: AsyncSession, 
        review_id: int, 
        is_visible: bool
    ) -> Optional[Review]:
        """Обновление видимости отзыва (для модераторов)"""
        review = await self.get_by_id(db, review_id)
        if not review:
            return None
        
        review.is_visible = is_visible
        await db.commit()
        await db.refresh(review)
        return review


# Экземпляр для использования в роутерах
review_crud = ReviewCRUD()
