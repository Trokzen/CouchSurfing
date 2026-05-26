"""
Listing Router - API endpoints для жилья
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date
import json

from app.core.database import get_db
from app.routers.auth import get_current_user
from app.models import User, UserRole
from app.schemas.listing import (
    ListingCreate, 
    ListingUpdate, 
    ListingResponse, 
    ListingSearchFilters,
    ListingBrief,
    ListingCreateWithImages
)
from app.services.listing import listing_service
from app.schemas.common import PaginatedResponse
from app.services.listing_image import listing_image_service
from app.schemas.listing_image import ListingImageCreate
import uuid
from pathlib import Path


router = APIRouter(prefix="/listings", tags=["Listings"])

# Директория для загрузки изображений
UPLOAD_DIR = Path(__file__).parent.parent / "uploads" / "listings"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/", response_model=ListingResponse, status_code=201)
async def create_listing(
    listing_data: ListingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Создать новое объявление о жилье.
    Доступно только для пользователей с ролью HOST.
    """
    return await listing_service.create_listing(
        db=db,
        listing_data=listing_data,
        user_id=current_user.id,
        user_role=current_user.role
    )


@router.post("/with-images", response_model=ListingResponse, status_code=201)
async def create_listing_with_images(
    title: str = Form(..., min_length=3, max_length=200),
    description: str = Form(..., min_length=10, max_length=5000),
    city: str = Form(..., min_length=2, max_length=100),
    address: str = Form(..., min_length=5, max_length=300),
    capacity: int = Form(..., ge=1, le=20),
    amenities: Optional[str] = Form(default="[]"),
    is_active: bool = Form(default=True),
    images: List[UploadFile] = File(default=None, description="Список изображений для загрузки"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Создать новое объявление о жилье с загрузкой изображений.
    Доступно только для пользователей с ролью HOST.
    
    Принимает FormData с полями:
    - title, description, city, address, capacity, amenities (JSON строка), is_active
    - images: список файлов изображений
    """
    # Парсим amenities из JSON строки
    try:
        amenities_list = json.loads(amenities) if amenities else []
        if not isinstance(amenities_list, list):
            amenities_list = [amenities_list]
    except json.JSONDecodeError:
        amenities_list = amenities.split(",") if amenities else []
    
    # Создаем объект ListingCreate
    listing_data = ListingCreate(
        title=title,
        description=description,
        city=city,
        address=address,
        capacity=capacity,
        amenities=amenities_list,
        is_active=is_active
    )
    
    # Создаем объявление
    listing = await listing_service.create_listing(
        db=db,
        listing_data=listing_data,
        user_id=current_user.id,
        user_role=current_user.role
    )
    
    # Если есть изображения, загружаем их
    if images:
        allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
        for idx, file in enumerate(images):
            if file.content_type not in allowed_types:
                continue
            
            # Генерация уникального имени файла
            file_extension = file.filename.split(".")[-1] if file.filename else "jpg"
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            file_path = UPLOAD_DIR / unique_filename
            
            # Сохранение файла
            try:
                with open(file_path, "wb") as buffer:
                    content = await file.read()
                    buffer.write(content)
            except Exception:
                continue
            
            # URL для доступа к файлу
            image_url = f"/static/listings/{unique_filename}"
            
            # Создание записи в БД
            image_data = ListingImageCreate(
                image_url=image_url,
                is_primary=(idx == 0)  # Первое изображение делаем главным
            )
            await listing_image_service.create_image_for_listing(
                db=db,
                listing_id=listing.id,
                image_data=image_data
            )
    
    # Обновляем listing с загруженными изображениями
    from app.crud.listing import listing_crud
    listing = await listing_crud.get_by_id(db, listing.id)
    
    return listing


@router.get("/", response_model=List[ListingBrief])
async def get_host_listings(
    host_id: int = Query(..., description="ID хоста"),
    include_inactive: bool = Query(False, description="Включая неактивные"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить список жилья конкретного хоста"""
    listings = await listing_service.get_host_listings(
        db=db,
        host_id=host_id,
        current_user_id=current_user.id,
        include_inactive=include_inactive
    )
    return listings


@router.get("/search", response_model=PaginatedResponse[ListingBrief])
async def search_listings(
    city: Optional[str] = Query(None, min_length=2, description="Город"),
    check_in: Optional[date] = Query(None, description="Дата заезда (YYYY-MM-DD)"),
    check_out: Optional[date] = Query(None, description="Дата выезда (YYYY-MM-DD)"),
    min_capacity: Optional[int] = Query(None, ge=1, description="Минимальная вместимость"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(20, ge=1, le=50, description="Размер страницы"),
    db: AsyncSession = Depends(get_db)
):
    """
    Поиск доступного жилья с фильтрами.
    
    Фильтры:
    - city: частичное совпадение по названию города
    - check_in/check_out: проверка на пересечение с существующими бронированиями
    - min_capacity: минимальная вместимость
    """
    filters = ListingSearchFilters(
        city=city,
        check_in=check_in,
        check_out=check_out,
        min_capacity=min_capacity,
        page=page,
        size=size
    )
    
    listings, total = await listing_service.search_listings(db, filters)
    
    return PaginatedResponse.create(
        items=listings,
        total=total,
        page=page,
        size=size
    )


@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing(
    listing_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить детальную информацию о жилье по ID"""
    return await listing_service.get_listing(db, listing_id)


@router.put("/{listing_id}", response_model=ListingResponse)
async def update_listing(
    listing_id: int,
    update_data: ListingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Обновить информацию о жилье.
    Доступно только владельцу жилья или модератору.
    """
    return await listing_service.update_listing(
        db=db,
        listing_id=listing_id,
        update_data=update_data,
        user_id=current_user.id,
        user_role=current_user.role
    )


@router.delete("/{listing_id}", status_code=204)
async def delete_listing(
    listing_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Удалить жилье (полное удаление из БД).
    Доступно только владельцу или модератору.
    """
    await listing_service.delete_listing(
        db=db,
        listing_id=listing_id,
        user_id=current_user.id,
        user_role=current_user.role
    )


@router.patch("/{listing_id}/toggle-active", response_model=ListingResponse)
async def toggle_listing_active(
    listing_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Переключить статус активности жилья (активен/неактивен).
    Доступно только владельцу жилья.
    """
    return await listing_service.toggle_active(
        db=db,
        listing_id=listing_id,
        user_id=current_user.id
    )


@router.get("/{listing_id}/availability")
async def check_availability(
    listing_id: int,
    start_date: date = Query(..., description="Дата начала"),
    end_date: date = Query(..., description="Дата окончания"),
    db: AsyncSession = Depends(get_db)
):
    """Проверить доступность жилья на указанные даты"""
    is_available = await listing_service.check_availability(
        db=db,
        listing_id=listing_id,
        start_date=start_date,
        end_date=end_date
    )
    return {"listing_id": listing_id, "available": is_available}
