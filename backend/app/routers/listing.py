"""
Listing Router - API endpoints для жилья
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date

from app.core.database import get_db
from app.routers.auth import get_current_user
from app.models import User, UserRole
from app.schemas.listing import (
    ListingCreate, 
    ListingUpdate, 
    ListingResponse, 
    ListingSearchFilters,
    ListingBrief
)
from app.services.listing import listing_service
from app.schemas.common import PaginatedResponse


router = APIRouter(prefix="/listings", tags=["Listings"])


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
