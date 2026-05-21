"""
Booking Schemas - Pydantic модели для бронирований
"""
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator
from enum import Enum


class BookingStatus(str, Enum):
    """
    Статусы бронирования (State Machine)
    
    Жизненный цикл:
    new -> pending -> confirmed -> completed
                      -> rejected
                -> cancelled
    """
    new = "new"           # Создано гостем
    pending = "pending"   # Ожидает подтверждения хоста
    confirmed = "confirmed"  # Подтверждено хостом
    rejected = "rejected"    # Отклонено хостом
    cancelled = "cancelled"  # Отменено гостем
    completed = "completed"  # Завершено (после выезда)


# ==================== Booking Create/Update ====================

class BookingCreate(BaseModel):
    """Схема создания нового бронирования"""
    listing_id: int
    start_date: date
    end_date: date
    message: Optional[str] = Field(None, max_length=500, description="Сообщение хосту")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "listing_id": 1,
                "start_date": "2025-06-01",
                "end_date": "2025-06-07",
                "message": "Hello! I'd love to stay at your place."
            }
        }
    )

    @model_validator(mode='after')
    def validate_dates(self) -> 'BookingCreate':
        """Проверка корректности дат"""
        if self.start_date >= self.end_date:
            raise ValueError("Дата выезда должна быть позже даты заезда")
        if self.start_date < date.today():
            raise ValueError("Дата заезда не может быть в прошлом")
        return self


class BookingUpdate(BaseModel):
    """Схема обновления бронирования (для внутренних операций)"""
    status: Optional[BookingStatus] = None
    # Другие поля могут добавляться по необходимости


# ==================== Booking Response ====================

class BookingResponse(BaseModel):
    """Схема ответа с данными бронирования"""
    id: int
    guest_id: int
    listing_id: int
    start_date: date
    end_date: date
    status: BookingStatus
    message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BookingWithDetailsResponse(BaseModel):
    """Бронирование с деталями жилья и пользователя"""
    id: int
    guest_id: int
    guest_name: str
    listing_id: int
    listing_title: str
    listing_city: str
    start_date: date
    end_date: date
    status: BookingStatus
    message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BookingBrief(BaseModel):
    """Краткая информация о бронировании для списков"""
    id: int
    listing_id: int
    listing_title: str
    start_date: date
    end_date: date
    status: BookingStatus

    model_config = ConfigDict(from_attributes=True)


# ==================== Status Change Requests ====================

class BookingStatusChange(BaseModel):
    """Запрос на изменение статуса бронирования"""
    status: BookingStatus
    reason: Optional[str] = Field(None, max_length=500, description="Причина изменения")

    @model_validator(mode='after')
    def validate_status_transition(self) -> 'BookingStatusChange':
        """
        Валидация допустимых переходов статусов
        
        Диаграмма переходов:
        - new -> pending, cancelled
        - pending -> confirmed, rejected, cancelled
        - confirmed -> cancelled, completed
        - rejected -> (terminal)
        - cancelled -> (terminal)
        - completed -> (terminal)
        """
        valid_transitions = {
            BookingStatus.new: [BookingStatus.pending, BookingStatus.cancelled],
            BookingStatus.pending: [BookingStatus.confirmed, BookingStatus.rejected, BookingStatus.cancelled],
            BookingStatus.confirmed: [BookingStatus.cancelled, BookingStatus.completed],
            BookingStatus.rejected: [],
            BookingStatus.cancelled: [],
            BookingStatus.completed: [],
        }
        
        # Примечание: полная валидация будет в сервисе, 
        # так как нужно знать текущий статус
        return self


# ==================== Availability Check ====================

class AvailabilityCheck(BaseModel):
    """Проверка доступности дат"""
    listing_id: int
    start_date: date
    end_date: date


class AvailabilityResponse(BaseModel):
    """Ответ о доступности"""
    is_available: bool
    conflicting_bookings: list[int] = Field(default_factory=list, description="ID конфликтующих бронирований")
    message: str
