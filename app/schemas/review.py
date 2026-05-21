"""
Review Schemas - Pydantic модели для отзывов
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator


# ==================== Review Create ====================

class ReviewCreate(BaseModel):
    """Схема создания отзыва"""
    booking_id: int
    target_id: int  # ID пользователя, которому оставляют отзыв
    rating: int = Field(..., ge=1, le=5, description="Рейтинг от 1 до 5")
    comment: str = Field(..., min_length=10, max_length=1000)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "booking_id": 42,
                "target_id": 15,
                "rating": 5,
                "comment": "Great host! The place was clean and exactly as described."
            }
        }
    )


# ==================== Review Response ====================

class ReviewResponse(BaseModel):
    """Схема ответа с данными отзыва"""
    id: int
    booking_id: int
    author_id: int
    author_name: str
    target_id: int
    target_name: str
    rating: int
    comment: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReviewBrief(BaseModel):
    """Краткая информация об отзыве"""
    id: int
    author_name: str
    rating: int
    comment: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== User Rating Summary ====================

class UserRatingSummary(BaseModel):
    """Сводная информация о рейтинге пользователя"""
    user_id: int
    average_rating: float
    total_reviews: int
    rating_distribution: dict[int, int] = Field(
        default_factory=lambda: {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
        description="Распределение оценок по звёздам"
    )

    model_config = ConfigDict(from_attributes=True)
