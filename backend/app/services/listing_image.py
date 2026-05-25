"""
Listing Image Service - Бизнес-логика для фотографий жилья
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.models import ListingImage, UserRole
from app.schemas.listing_image import ListingImageCreate, ListingImageUpdate, ListingImageResponse
from app.crud.listing_image import listing_image_crud
from app.core.exceptions import (
    NotFoundException as NotFoundError,
    AuthorizationException as ForbiddenError,
)
from app.services.listing import listing_service


class ListingImageService:
    """Сервис для управления фотографиями жилья"""
    
    async def upload_image(
        self,
        db: AsyncSession,
        listing_id: int,
        image_data: ListingImageCreate,
        user_id: int,
        user_role: UserRole
    ) -> ListingImage:
        """
        Загрузка новой фотографии жилья.
        Только владелец жилья может добавлять фото.
        """
        # Проверка существования жилья и прав доступа
        listing = await listing_service.get_listing(db, listing_id)
        
        if listing.host_id != user_id and user_role != UserRole.MODERATOR:
            raise ForbiddenError("Только владелец жилья может добавлять фотографии")
        
        return await listing_image_crud.create(db, image_data, listing_id)
    
    async def get_images(self, db: AsyncSession, listing_id: int) -> List[ListingImage]:
        """Получение всех фотографий жилья"""
        # Проверка существования жилья
        await listing_service.get_listing(db, listing_id)
        return await listing_image_crud.get_listing_images(db, listing_id)
    
    async def update_image(
        self,
        db: AsyncSession,
        image_id: int,
        update_data: ListingImageUpdate,
        user_id: int,
        user_role: UserRole
    ) -> ListingImage:
        """
        Обновление фотографии.
        Только владелец жилья может редактировать фото.
        """
        image = await listing_image_crud.get_by_id(db, image_id)
        if not image:
            raise NotFoundError(f"Фотография с ID {image_id} не найдена")
        
        # Проверка прав доступа через владельца жилья
        listing = await listing_service.get_listing(db, image.listing_id)
        if listing.host_id != user_id and user_role != UserRole.MODERATOR:
            raise ForbiddenError("Только владелец жилья может редактировать фотографии")
        
        updated_image = await listing_image_crud.update(db, image_id, update_data)
        return updated_image
    
    async def delete_image(
        self,
        db: AsyncSession,
        image_id: int,
        user_id: int,
        user_role: UserRole
    ) -> bool:
        """
        Удаление фотографии.
        Только владелец жилья может удалять фото.
        """
        image = await listing_image_crud.get_by_id(db, image_id)
        if not image:
            raise NotFoundError(f"Фотография с ID {image_id} не найдена")
        
        # Проверка прав доступа через владельца жилья
        listing = await listing_service.get_listing(db, image.listing_id)
        if listing.host_id != user_id and user_role != UserRole.MODERATOR:
            raise ForbiddenError("Только владелец жилья может удалять фотографии")
        
        return await listing_image_crud.delete(db, image_id)


# Экземпляр сервиса
listing_image_service = ListingImageService()
