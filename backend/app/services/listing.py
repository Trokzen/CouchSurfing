"""
Listing Service - Бизнес-логика для жилья
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Tuple
from datetime import date

from app.models import Listing, UserRole
from app.schemas.listing import ListingCreate, ListingUpdate, ListingSearchFilters, ListingBrief
from app.crud.listing import listing_crud
from app.core.exceptions import (
    NotFoundException as NotFoundError,
    AuthorizationException as ForbiddenError,
    ValidationException as ValidationError
)


class ListingService:
    """Сервис для управления жильем"""
    
    async def create_listing(
        self,
        db: AsyncSession,
        listing_data: ListingCreate,
        user_id: int,
        user_role: UserRole
    ) -> Listing:
        """
        Создание нового жилья.
        Только пользователи с ролью HOST могут создавать listings.
        """
        if user_role != UserRole.HOST:
            raise ForbiddenError("Только хосты могут создавать объявления о жилье")
        
        return await listing_crud.create(db, listing_data, host_id=user_id)
    
    async def get_listing(self, db: AsyncSession, listing_id: int) -> Listing:
        """Получение информации о жилье по ID"""
        listing = await listing_crud.get_by_id(db, listing_id)
        if not listing:
            raise NotFoundError(f"Жилье с ID {listing_id} не найдено")
        return listing
    
    async def get_host_listings(
        self,
        db: AsyncSession,
        host_id: int,
        current_user_id: int,
        include_inactive: bool = False
    ) -> List[Listing]:
        """
        Получение списка жилья хоста.
        Пользователь может видеть только свои listings или все активные.
        """
        # Если пользователь запрашивает не свои listings, показываем только активные
        if host_id != current_user_id:
            include_inactive = False
        
        return await listing_crud.get_host_listings(db, host_id, include_inactive)
    
    async def update_listing(
        self,
        db: AsyncSession,
        listing_id: int,
        update_data: ListingUpdate,
        user_id: int,
        user_role: UserRole
    ) -> Listing:
        """
        Обновление жилья.
        Только владелец (host) может редактировать свое жилье.
        """
        listing = await self.get_listing(db, listing_id)
        
        # Проверка прав доступа
        if listing.host_id != user_id and user_role != UserRole.MODERATOR:
            raise ForbiddenError("Только владелец жилья может его редактировать")
        
        updated_listing = await listing_crud.update(db, listing_id, update_data)
        return updated_listing
    
    async def delete_listing(
        self,
        db: AsyncSession,
        listing_id: int,
        user_id: int,
        user_role: UserRole
    ) -> bool:
        """
        Удаление жилья (полное удаление из БД).
        Только владелец или модератор может удалить жилье.
        """
        listing = await self.get_listing(db, listing_id)
        
        # Проверка прав доступа
        if listing.host_id != user_id and user_role != UserRole.MODERATOR:
            raise ForbiddenError("Только владелец жилья может его удалить")
        
        return await listing_crud.hard_delete(db, listing_id)
    
    async def search_listings(
        self,
        db: AsyncSession,
        filters: ListingSearchFilters
    ) -> Tuple[List[ListingBrief], int]:
        """Поиск жилья с фильтрами"""
        if not filters.validate_dates():
            raise ValidationError("Дата выезда должна быть позже даты заезда")
        
        return await listing_crud.search(db, filters)
    
    async def check_availability(
        self,
        db: AsyncSession,
        listing_id: int,
        start_date: date,
        end_date: date
    ) -> bool:
        """Проверка доступности жилья на даты"""
        await self.get_listing(db, listing_id)  # Проверка существования
        return await listing_crud.check_availability(db, listing_id, start_date, end_date)

    async def toggle_active(
        self,
        db: AsyncSession,
        listing_id: int,
        user_id: int
    ) -> Listing:
        """Переключение статуса активности жилья"""
        listing = await self.get_listing(db, listing_id)
        
        # Проверка прав доступа
        if listing.host_id != user_id:
            raise ForbiddenError("Только владелец жилья может изменять его статус")
        
        return await listing_crud.toggle_active(db, listing_id)


# Экземпляр сервиса
listing_service = ListingService()
