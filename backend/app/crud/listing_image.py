"""
Listing Image CRUD Operations - Асинхронные операции с фотографиями жилья
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.models import ListingImage
from app.schemas.listing_image import ListingImageCreate, ListingImageUpdate


class ListingImageCRUD:
    """Класс для операций с фотографиями жилья в БД"""
    
    async def create(
        self, 
        db: AsyncSession, 
        image_data: ListingImageCreate, 
        listing_id: int
    ) -> ListingImage:
        """Создание новой фотографии жилья"""
        # Если это главное фото, сбросим is_primary у других фото этого listing
        if image_data.is_primary:
            await self._reset_primary_images(db, listing_id)
        
        image = ListingImage(
            listing_id=listing_id,
            **image_data.model_dump()
        )
        db.add(image)
        await db.commit()
        await db.refresh(image)
        return image
    
    async def get_by_id(self, db: AsyncSession, image_id: int) -> Optional[ListingImage]:
        """Получение фотографии по ID"""
        result = await db.execute(
            select(ListingImage).where(ListingImage.id == image_id)
        )
        return result.scalar_one_or_none()
    
    async def get_listing_images(self, db: AsyncSession, listing_id: int) -> List[ListingImage]:
        """Получение всех фотографий жилья"""
        result = await db.execute(
            select(ListingImage)
            .where(ListingImage.listing_id == listing_id)
            .order_by(ListingImage.is_primary.desc(), ListingImage.created_at.asc())
        )
        return list(result.scalars().all())
    
    async def update(
        self, 
        db: AsyncSession, 
        image_id: int, 
        update_data: ListingImageUpdate
    ) -> Optional[ListingImage]:
        """Обновление фотографии"""
        image = await self.get_by_id(db, image_id)
        if not image:
            return None
        
        update_dict = update_data.model_dump(exclude_unset=True)
        
        # Если устанавливаем is_primary=True, сбросим у других
        if update_dict.get("is_primary"):
            await self._reset_primary_images(db, image.listing_id)
        
        for field, value in update_dict.items():
            setattr(image, field, value)
        
        await db.commit()
        await db.refresh(image)
        return image
    
    async def delete(self, db: AsyncSession, image_id: int) -> bool:
        """Удаление фотографии"""
        image = await self.get_by_id(db, image_id)
        if not image:
            return False
        
        await db.delete(image)
        await db.commit()
        return True
    
    async def _reset_primary_images(self, db: AsyncSession, listing_id: int) -> None:
        """Сбросить флаг is_primary у всех фотографий жилья"""
        images = await self.get_listing_images(db, listing_id)
        for image in images:
            if image.is_primary:
                image.is_primary = False
        await db.commit()


# Экземпляр для использования в роутерах
listing_image_crud = ListingImageCRUD()
