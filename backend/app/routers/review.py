"""
Review Router - API endpoints для отзывов
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User, UserRole
from app.schemas.review import (
    ReviewCreate, 
    ReviewResponse, 
    ReviewBrief,
    UserRatingSummary
)
from app.services.review import review_service


router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("/", response_model=ReviewResponse, status_code=201)
async def create_review(
    review_data: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Создать отзыв о пользователе.
    
    Требования:
    - Пользователь должен быть участником завершенного бронирования
    - Бронирование должно иметь статус 'completed'
    - Нельзя оставить повторный отзыв для того же бронирования
    - Отзыв можно оставить только противоположной стороне (гость -> хост, хост -> гость)
    """
    return await review_service.create_review(
        db=db,
        review_data=review_data,
        author_id=current_user.id
    )


@router.get("/user/{user_id}", response_model=UserRatingSummary)
async def get_user_reviews(
    user_id: int = Path(..., gt=0, description="ID пользователя"),
    db: AsyncSession = Depends(get_db)
):
    """
    Получить отзывы и рейтинг пользователя.
    
    Возвращает сводную информацию:
    - Средний рейтинг
    - Общее количество отзывов
    - Распределение по оценкам
    - Последние 5 отзывов
    """
    return await review_service.get_user_rating_summary(db, user_id)


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: int = Path(..., gt=0, description="ID отзыва"),
    db: AsyncSession = Depends(get_db)
):
    """Получить отзыв по ID"""
    return await review_service.get_review(db, review_id)


@router.post("/{review_id}/hide")
async def hide_review(
    review_id: int = Path(..., gt=0, description="ID отзыва"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Скрыть отзыв (только для модераторов).
    
    Используется для модерации некорректных или нарушающих правила отзывов.
    """
    if current_user.role != UserRole.MODERATOR:
        raise HTTPException(
            status_code=403,
            detail="Только модератор может скрывать отзывы"
        )
    
    return await review_service.hide_review(
        db=db,
        review_id=review_id,
        moderator_id=current_user.id
    )


@router.post("/{review_id}/show")
async def show_review(
    review_id: int = Path(..., gt=0, description="ID отзыва"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Показать скрытый отзыв (только для модераторов).
    """
    if current_user.role != UserRole.MODERATOR:
        raise HTTPException(
            status_code=403,
            detail="Только модератор может показывать отзывы"
        )
    
    return await review_service.show_review(
        db=db,
        review_id=review_id,
        moderator_id=current_user.id
    )


@router.get("/booking/{booking_id}/can-review")
async def can_leave_review(
    booking_id: int = Path(..., gt=0, description="ID бронирования"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Проверить возможность оставить отзыв для указанного бронирования.
    
    Возвращает:
    - can_review: bool - можно ли оставить отзыв
    - reason: str - причина если нельзя (пустая строка если можно)
    - target_id: int | null - ID пользователя которому можно оставить отзыв
    """
    from app.crud.review import review_crud
    from app.crud.booking import booking_crud
    
    # Проверяем возможность
    can_review, reason = await review_crud.can_review_booking(
        db=db,
        booking_id=booking_id,
        user_id=current_user.id
    )
    
    target_id = None
    if can_review:
        # Загружаем бронирование чтобы определить target_id
        booking = await booking_crud.get_by_id(db, booking_id)
        if booking:
            is_guest = (booking.guest_id == current_user.id)
            if is_guest and booking.listing:
                target_id = booking.listing.host_id
            elif not is_guest:
                target_id = booking.guest_id
    
    return {
        "can_review": can_review,
        "reason": reason,
        "target_id": target_id,
        "booking_id": booking_id
    }
