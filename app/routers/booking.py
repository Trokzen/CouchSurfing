"""
Booking Router - API endpoints для бронирований
"""
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User, UserRole, BookingStatus
from app.schemas.booking import (
    BookingCreate, 
    BookingResponse, 
    BookingWithDetailsResponse,
    BookingBrief,
    BookingStatusChange
)
from app.services.booking import booking_service


router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("/", response_model=BookingResponse, status_code=201)
async def create_booking(
    booking_data: BookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Создать новое бронирование.
    
    Гость создает заявку на бронирование жилья.
    После создания статус автоматически устанавливается в 'pending'
    (ожидает подтверждения хоста).
    
    Требования:
    - Пользователь должен быть аутентифицирован
    - Даты должны быть доступны (не пересекаться с другими бронированиями)
    - Жилье должно существовать и быть активным
    """
    return await booking_service.create_booking(
        db=db,
        booking_data=booking_data,
        guest_id=current_user.id
    )


@router.get("/my", response_model=List[BookingBrief])
async def get_my_bookings(
    status: Optional[BookingStatus] = Query(None, description="Фильтр по статусу"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить все мои бронирования (как гость)"""
    bookings = await booking_service.get_guest_bookings(
        db=db,
        guest_id=current_user.id,
        status=status
    )
    return bookings


@router.get("/host", response_model=List[BookingBrief])
async def get_host_bookings(
    status: Optional[BookingStatus] = Query(None, description="Фильтр по статусу"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получить все бронирования моего жилья (как хост).
    Доступно только для пользователей с ролью HOST.
    """
    if current_user.role != UserRole.HOST:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только хосты могут просматривать бронирования своего жилья"
        )
    
    bookings = await booking_service.get_host_bookings(
        db=db,
        host_id=current_user.id,
        status=status
    )
    return bookings


@router.get("/{booking_id}", response_model=BookingWithDetailsResponse)
async def get_booking(
    booking_id: int = Path(..., gt=0, description="ID бронирования"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получить детальную информацию о бронировании.
    
    Доступно:
    - Гостю который создал бронирование
    - Хосту которому принадлежит жилье
    - Модератору
    """
    booking = await booking_service.get_booking(db, booking_id)
    
    # Проверка прав доступа
    is_owner = (booking.guest_id == current_user.id)
    is_host = False
    
    if booking.listing:
        is_host = (booking.listing.host_id == current_user.id)
    
    if not is_owner and not is_host and current_user.role != UserRole.MODERATOR:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав на просмотр этого бронирования"
        )
    
    # Формируем расширенный ответ
    return BookingWithDetailsResponse(
        id=booking.id,
        guest_id=booking.guest_id,
        guest_name=booking.guest.full_name if booking.guest else "Unknown",
        listing_id=booking.listing_id,
        listing_title=booking.listing.title if booking.listing else "Unknown",
        listing_city=booking.listing.city if booking.listing else "Unknown",
        start_date=booking.start_date,
        end_date=booking.end_date,
        status=booking.status,
        message=booking.message,
        created_at=booking.created_at,
        updated_at=booking.updated_at
    )


@router.post("/{booking_id}/confirm", response_model=BookingResponse)
async def confirm_booking(
    booking_id: int = Path(..., gt=0, description="ID бронирования"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Подтвердить бронирование (как хост).
    
    Переводит бронирование из статуса 'pending' в 'confirmed'.
    После подтверждения даты считаются занятыми.
    """
    if current_user.role != UserRole.HOST and current_user.role != UserRole.MODERATOR:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только хост может подтвердить бронирование"
        )
    
    return await booking_service.confirm_booking(
        db=db,
        booking_id=booking_id,
        host_id=current_user.id
    )


@router.post("/{booking_id}/reject", response_model=BookingResponse)
async def reject_booking(
    booking_id: int = Path(..., gt=0, description="ID бронирования"),
    reason: Optional[str] = Query(None, max_length=500, description="Причина отклонения"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Отклонить бронирование (как хост).
    
    Переводит бронирование из статуса 'pending' в 'rejected'.
    Освобождает даты (если были предварительно зарезервированы).
    """
    if current_user.role != UserRole.HOST and current_user.role != UserRole.MODERATOR:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только хост может отклонить бронирование"
        )
    
    return await booking_service.reject_booking(
        db=db,
        booking_id=booking_id,
        host_id=current_user.id,
        reason=reason
    )


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: int = Path(..., gt=0, description="ID бронирования"),
    reason: Optional[str] = Query(None, max_length=500, description="Причина отмены"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Отменить бронирование (как гость).
    
    Переводит бронирование в статус 'cancelled'.
    Доступно для статусов: new, pending, confirmed.
    """
    return await booking_service.cancel_booking(
        db=db,
        booking_id=booking_id,
        user_id=current_user.id,
        reason=reason
    )


@router.post("/{booking_id}/complete", response_model=BookingResponse)
async def complete_booking(
    booking_id: int = Path(..., gt=0, description="ID бронирования"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Завершить бронирование (как хост).
    
    Переводит бронирование из статуса 'confirmed' в 'completed'.
    Доступно только после даты выезда.
    После завершения можно оставить отзыв.
    """
    if current_user.role != UserRole.HOST and current_user.role != UserRole.MODERATOR:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только хост может завершить бронирование"
        )
    
    return await booking_service.complete_booking(
        db=db,
        booking_id=booking_id,
        host_id=current_user.id
    )


@router.get("/{booking_id}/status-transitions")
async def get_available_transitions(
    booking_id: int = Path(..., gt=0, description="ID бронирования"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получить доступные переходы статусов для данного бронирования.
    
    Возвращает список статусов, в которые можно перевести текущее бронирование
    с учетом роли пользователя.
    """
    booking = await booking_service.get_booking(db, booking_id)
    
    from app.services.booking import VALID_TRANSITIONS
    
    current_status = booking.status
    all_possible_transitions = VALID_TRANSITIONS.get(current_status, [])
    
    # Фильтруем по правам пользователя
    is_owner = (booking.guest_id == current_user.id)
    is_host = False
    
    if booking.listing:
        is_host = (booking.listing.host_id == current_user.id)
    
    allowed_transitions = []
    
    for status in all_possible_transitions:
        if status == BookingStatus.CANCELLED and (is_owner or current_user.role == UserRole.MODERATOR):
            allowed_transitions.append(status.value)
        elif status in [BookingStatus.CONFIRMED, BookingStatus.REJECTED] and (is_host or current_user.role == UserRole.MODERATOR):
            allowed_transitions.append(status.value)
        elif status == BookingStatus.COMPLETED and (is_host or current_user.role == UserRole.MODERATOR):
            allowed_transitions.append(status.value)
    
    return {
        "booking_id": booking_id,
        "current_status": current_status.value,
        "available_transitions": allowed_transitions
    }
