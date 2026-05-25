"""
Listing Image Router - API endpoints для фотографий жилья
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import os
import uuid
from pathlib import Path

from app.core.database import get_db
from app.routers.auth import get_current_user
from app.models import User, UserRole
from app.schemas.listing_image import ListingImageCreate, ListingImageUpdate, ListingImageResponse
from app.services.listing_image import listing_image_service
from app.core.config import get_settings

settings = get_settings()

router = APIRouter(prefix="/listings", tags=["Listing Images"])

# Директория для загрузки изображений
UPLOAD_DIR = Path("uploads/listings")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/{listing_id}/images", response_model=ListingImageResponse, status_code=201)
async def upload_listing_image(
    listing_id: int,
    file: UploadFile = File(..., description="Файл изображения"),
    is_primary: bool = Form(False, description="Является ли главное фотографией"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Загрузить фотографию для жилья.
    Только владелец жилья может добавлять фото.
    """
    # Проверка типа файла
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Недопустимый тип файла. Разрешены: {', '.join(allowed_types)}"
        )
    
    # Генерация уникального имени файла
    file_extension = file.filename.split(".")[-1] if file.filename else "jpg"
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Сохранение файла
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения файла: {str(e)}")
    
    # URL для доступа к файлу
    image_url = f"/static/uploads/listings/{unique_filename}"
    
    # Создание записи в БД
    image_data = ListingImageCreate(image_url=image_url, is_primary=is_primary)
    return await listing_image_service.upload_image(
        db=db,
        listing_id=listing_id,
        image_data=image_data,
        user_id=current_user.id,
        user_role=current_user.role
    )


@router.get("/{listing_id}/images", response_model=List[ListingImageResponse])
async def get_listing_images(
    listing_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить все фотографии жилья"""
    return await listing_image_service.get_images(db, listing_id)


@router.put("/images/{image_id}", response_model=ListingImageResponse)
async def update_listing_image(
    image_id: int,
    is_primary: bool = Form(..., description="Является ли главное фотографией"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Обновить информацию о фотографии (например, установить как главную).
    Только владелец жилья может редактировать фото.
    """
    update_data = ListingImageUpdate(is_primary=is_primary)
    return await listing_image_service.update_image(
        db=db,
        image_id=image_id,
        update_data=update_data,
        user_id=current_user.id,
        user_role=current_user.role
    )


@router.delete("/images/{image_id}", status_code=204)
async def delete_listing_image(
    image_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Удалить фотографию жилья.
    Только владелец жилья может удалять фото.
    """
    # Получаем информацию о фото перед удалением для удаления файла
    from app.crud.listing_image import listing_image_crud
    image = await listing_image_crud.get_by_id(db, image_id)
    
    if not image:
        raise HTTPException(status_code=404, detail="Фотография не найдена")
    
    # Удаляем запись из БД
    success = await listing_image_service.delete_image(
        db=db,
        image_id=image_id,
        user_id=current_user.id,
        user_role=current_user.role
    )
    
    if success:
        # Удаляем файл с диска
        file_path = str(UPLOAD_DIR / image.image_url.split("/")[-1])
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass  # Игнорируем ошибки удаления файла
    
    return None
