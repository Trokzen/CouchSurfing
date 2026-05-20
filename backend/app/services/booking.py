"""
Booking Service - Бизнес-логика для бронирований (State Machine)
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date

from app.models import Booking, UserRole, BookingStatus
from app.schemas.booking import BookingCreate, BookingStatusChange
from app.crud.booking import booking_crud
from app.crud.listing import listing_crud
from app.core.exceptions import (
    NotFoundException,
    AuthorizationException,
    ValidationException,
    ConflictException
)


# Допустимые переходы статусов (State Machine)
VALID_TRANSITIONS = {
    BookingStatus.NEW: [BookingStatus.PENDING, BookingStatus.CANCELLED],
    BookingStatus.PENDING: [BookingStatus.CONFIRMED, BookingStatus.REJECTED, BookingStatus.CANCELLED],
    BookingStatus.CONFIRMED: [BookingStatus.CANCELLED, BookingStatus.COMPLETED],
    BookingStatus.REJECTED: [],  # Терминальный статус
    BookingStatus.CANCELLED: [],  # Терминальный статус
    BookingStatus.COMPLETED: [],  # Терминальный статус
}


class BookingService:
    """Сервис для управления бронированиями"""
    
    async def create_booking(
        self,
        db: AsyncSession,
        booking_data: BookingCreate,
        guest_id: int
    ) -> Booking:
        """
        Создание нового бронирования.
        
        Логика:
        1. Проверяем существование жилья
        2. Проверяем доступность дат (нет ли пересечений)
        3. Создаем бронирование со статусом 'new'
        4. Автоматически переводим в 'pending' (ожидание подтверждения хоста)
        """
        # Проверка существования жилья
        listing = await listing_crud.get_by_id(db, booking_data.listing_id)
        if not listing:
            raise NotFoundException(f"Жилье с ID {booking_data.listing_id} не найдено")
        
        if not listing.is_active:
            raise ValidationException("Это жилье больше не доступно для бронирования")
        
        # Проверка вместимости
        if booking_data.guest_count if hasattr(booking_data, 'guest_count') else 1 > listing.capacity:
            raise ValidationException(
                f"Вместимость жилья: {listing.capacity} чел., запрошено: {booking_data.guest_count if hasattr(booking_data, 'guest_count') else 1}"
            )
        
        # Проверка доступности дат
        conflicts = await booking_crud.check_date_conflict(
            db,
            listing_id=booking_data.listing_id,
            start_date=booking_data.start_date,
            end_date=booking_data.end_date
        )
        
        if conflicts:
            raise ConflictException(
                f"Выбранные даты уже забронированы (конфликтующих бронирований: {len(conflicts)})"
            )
        
        # Создание бронирования
        booking = await booking_crud.create(db, booking_data, guest_id)
        
        # Автоматический переход в pending (отправка запроса хосту)
        booking = await booking_crud.update_status(db, booking.id, BookingStatus.PENDING)
        
        return booking
    
    async def get_booking(self, db: AsyncSession, booking_id: int) -> Booking:
        """Получение бронирования по ID"""
        booking = await booking_crud.get_by_id(db, booking_id)
        if not booking:
            raise NotFoundException(f"Бронирование с ID {booking_id} не найдено")
        return booking
    
    async def get_guest_bookings(
        self,
        db: AsyncSession,
        guest_id: int,
        status: Optional[BookingStatus] = None
    ) -> List[Booking]:
        """Получение всех бронирований гостя"""
        return await booking_crud.get_guest_bookings(db, guest_id, status)
    
    async def get_host_bookings(
        self,
        db: AsyncSession,
        host_id: int,
        status: Optional[BookingStatus] = None
    ) -> List[Booking]:
        """Получение всех бронирований жилья хоста"""
        return await booking_crud.get_host_bookings(db, host_id, status)
    
    async def change_status(
        self,
        db: AsyncSession,
        booking_id: int,
        new_status: BookingStatus,
        user_id: int,
        user_role: UserRole,
        reason: Optional[str] = None
    ) -> Booking:
        """
        Изменение статуса бронирования (State Machine).
        
        Правила доступа:
        - Гость может: cancel (из new/pending/confirmed)
        - Хост может: confirm/reject (из pending), complete (из confirmed)
        - Модератор может: любые изменения
        
        Валидация переходов:
        - new -> pending, cancelled
        - pending -> confirmed, rejected, cancelled
        - confirmed -> cancelled, completed
        - rejected/cancelled/completed -> терминальные (нельзя изменить)
        """
        booking = await self.get_booking(db, booking_id)
        current_status = booking.status
        
        # Проверка допустимости перехода
        if new_status not in VALID_TRANSITIONS.get(current_status, []):
            raise ValidationException(
                f"Недопустимый переход статуса: {current_status.value} -> {new_status.value}. "
                f"Допустимые переходы: {[s.value for s in VALID_TRANSITIONS.get(current_status, [])]}"
            )
        
        # Проверка прав доступа
        is_owner = (booking.guest_id == user_id)
        is_host = False
        
        if booking.listing:
            is_host = (booking.listing.host_id == user_id)
        
        # Проверка прав на изменение статуса
        if user_role != UserRole.MODERATOR:
            if new_status in [BookingStatus.CANCELLED]:
                # Отменить может только гость
                if not is_owner and user_role != UserRole.MODERATOR:
                    raise AuthorizationException("Только гость может отменить бронирование")
            
            elif new_status in [BookingStatus.CONFIRMED, BookingStatus.REJECTED]:
                # Подтвердить/отклонить может только хост
                if not is_host and user_role != UserRole.MODERATOR:
                    raise AuthorizationException("Только владелец жилья может подтвердить или отклонить бронирование")
            
            elif new_status == BookingStatus.COMPLETED:
                # Завершить может только хост (после выезда)
                if not is_host and user_role != UserRole.MODERATOR:
                    raise AuthorizationException("Только владелец жилья может завершить бронирование")
        
        # Дополнительная проверка: нельзя завершить бронирование если дата выезда в будущем
        if new_status == BookingStatus.COMPLETED:
            from datetime import date as dt
            if booking.end_date > dt.today():
                raise ValidationException(
                    "Нельзя завершить бронирование до даты выезда"
                )
        
        # Обновление статуса
        updated_booking = await booking_crud.update_status(db, booking_id, new_status)
        return updated_booking
    
    async def cancel_booking(
        self,
        db: AsyncSession,
        booking_id: int,
        user_id: int,
        reason: Optional[str] = None
    ) -> Booking:
        """Отмена бронирования гостем"""
        return await self.change_status(
            db=db,
            booking_id=booking_id,
            new_status=BookingStatus.CANCELLED,
            user_id=user_id,
            user_role=UserRole.GUEST,
            reason=reason
        )
    
    async def confirm_booking(
        self,
        db: AsyncSession,
        booking_id: int,
        host_id: int
    ) -> Booking:
        """Подтверждение бронирования хостом"""
        # Финальная проверка доступности дат перед подтверждением
        booking = await self.get_booking(db, booking_id)
        
        conflicts = await booking_crud.check_date_conflict(
            db,
            listing_id=booking.listing_id,
            start_date=booking.start_date,
            end_date=booking.end_date,
            exclude_booking_id=booking.id
        )
        
        if conflicts:
            raise ConflictException(
                "Невозможно подтвердить бронирование: даты были заняты другим бронированием"
            )
        
        return await self.change_status(
            db=db,
            booking_id=booking_id,
            new_status=BookingStatus.CONFIRMED,
            user_id=host_id,
            user_role=UserRole.HOST
        )
    
    async def reject_booking(
        self,
        db: AsyncSession,
        booking_id: int,
        host_id: int,
        reason: Optional[str] = None
    ) -> Booking:
        """Отклонение бронирования хостом"""
        return await self.change_status(
            db=db,
            booking_id=booking_id,
            new_status=BookingStatus.REJECTED,
            user_id=host_id,
            user_role=UserRole.HOST,
            reason=reason
        )
    
    async def complete_booking(
        self,
        db: AsyncSession,
        booking_id: int,
        host_id: int
    ) -> Booking:
        """Завершение бронирования хостом (после выезда)"""
        return await self.change_status(
            db=db,
            booking_id=booking_id,
            new_status=BookingStatus.COMPLETED,
            user_id=host_id,
            user_role=UserRole.HOST
        )


# Экземпляр сервиса
booking_service = BookingService()
