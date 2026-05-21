"""
Review Service - Бизнес-логика для отзывов
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.models import Review, User, UserRole
from app.schemas.review import ReviewCreate, ReviewResponse, UserRatingSummary
from app.crud.review import review_crud
from app.crud.booking import booking_crud
from app.core.exceptions import (
    NotFoundException,
    AuthorizationException,
    ValidationException,
    ConflictException
)


class ReviewService:
    """Сервис для управления отзывами"""
    
    async def create_review(
        self,
        db: AsyncSession,
        review_data: ReviewCreate,
        author_id: int
    ) -> Review:
        """
        Создание нового отзыва.
        
        Правила:
        1. Отзыв можно оставить только для завершенного бронирования (status = completed)
        2. Пользователь должен быть участником бронирования (гость или хост)
        3. Нельзя оставить повторный отзыв для того же бронирования
        """
        # Проверка возможности оставить отзыв
        can_review, reason = await review_crud.can_review_booking(
            db=db,
            booking_id=review_data.booking_id,
            user_id=author_id
        )
        
        if not can_review:
            raise ValidationException(reason)
        
        # Загружаем бронирование чтобы определить target_id
        booking = await booking_crud.get_by_id(db, review_data.booking_id)
        if not booking:
            raise NotFoundException(f"Бронирование с ID {review_data.booking_id} не найдено")
        
        # Определяем цель отзыва (противоположная сторона в бронировании)
        is_guest = (booking.guest_id == author_id)
        if is_guest:
            # Гость оставляет отзыв хосту
            expected_target = booking.listing.host_id if booking.listing else None
            if expected_target != review_data.target_id:
                raise ValidationException("Некорректный target_id. Для гостя целью отзыва должен быть хост.")
        else:
            # Хост оставляет отзыв гостю
            if booking.guest_id != review_data.target_id:
                raise ValidationException("Некорректный target_id. Для хоста целью отзыва должен быть гость.")
        
        # Создание отзыва
        review = await review_crud.create(db, review_data, author_id)
        return review
    
    async def get_user_reviews(
        self,
        db: AsyncSession,
        user_id: int,
        limit: int = 10
    ) -> List[Review]:
        """Получение отзывов для пользователя"""
        return await review_crud.get_reviews_for_user(db, user_id, limit)
    
    async def get_user_rating_summary(
        self,
        db: AsyncSession,
        user_id: int
    ) -> UserRatingSummary:
        """Получение сводной информации о рейтинге пользователя"""
        # Получаем данные о рейтинге
        avg_rating, total_reviews, distribution = await review_crud.get_user_rating_summary(db, user_id)
        
        # Получаем имя пользователя
        from app.crud.user import user_crud
        user = await user_crud.get_by_id(db, user_id)
        if not user:
            raise NotFoundException(f"Пользователь с ID {user_id} не найден")
        
        # Получаем краткие отзывы
        reviews = await review_crud.get_reviews_for_user(db, user_id, limit=5)
        
        return UserRatingSummary(
            user_id=user_id,
            average_rating=avg_rating,
            total_reviews=total_reviews,
            rating_distribution=distribution,
            reviews=[
                {
                    "id": r.id,
                    "author_name": r.author.full_name if r.author else "Unknown",
                    "rating": r.rating,
                    "comment": r.comment,
                    "created_at": r.created_at
                }
                for r in reviews
            ]
        )
    
    async def get_review(self, db: AsyncSession, review_id: int) -> Review:
        """Получение отзыва по ID"""
        review = await review_crud.get_by_id(db, review_id)
        if not review:
            raise NotFoundException(f"Отзыв с ID {review_id} не найден")
        return review
    
    async def hide_review(
        self,
        db: AsyncSession,
        review_id: int,
        moderator_id: int
    ) -> Review:
        """Скрытие отзыва модератором"""
        # Проверка что пользователь модератор
        from app.crud.user import user_crud
        moderator = await user_crud.get_by_id(db, moderator_id)
        if not moderator or moderator.role != UserRole.MODERATOR:
            raise AuthorizationException("Только модератор может скрывать отзывы")
        
        review = await self.get_review(db, review_id)
        updated_review = await review_crud.update_visibility(db, review_id, False)
        return updated_review
    
    async def show_review(
        self,
        db: AsyncSession,
        review_id: int,
        moderator_id: int
    ) -> Review:
        """Показ скрытого отзыва модератором"""
        # Проверка что пользователь модератор
        from app.crud.user import user_crud
        moderator = await user_crud.get_by_id(db, moderator_id)
        if not moderator or moderator.role != UserRole.MODERATOR:
            raise AuthorizationException("Только модератор может показывать отзывы")
        
        review = await self.get_review(db, review_id)
        updated_review = await review_crud.update_visibility(db, review_id, True)
        return updated_review


# Экземпляр сервиса
review_service = ReviewService()
