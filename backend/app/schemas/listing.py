"""
Listing Schemas - Pydantic модели для жилья
"""
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator


# ==================== Listing Create/Update ====================

class ListingCreate(BaseModel):
    """Схема создания нового жилья"""
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)
    city: str = Field(..., min_length=2, max_length=100)
    address: str = Field(..., min_length=5, max_length=300)
    capacity: int = Field(..., ge=1, le=20, description="Вместимость в людях")
    amenities: Optional[List[str]] = Field(default_factory=list, description="Удобства")
    is_active: bool = True

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Cozy Studio in City Center",
                "description": "Beautiful studio apartment with great view...",
                "city": "Moscow",
                "address": "Tverskaya St, 15, Apt 42",
                "capacity": 2,
                "amenities": ["wifi", "kitchen", "washing_machine"],
                "is_active": True
            }
        }
    )


class ListingUpdate(BaseModel):
    """Схема обновления жилья"""
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=5000)
    city: Optional[str] = Field(None, min_length=2, max_length=100)
    address: Optional[str] = Field(None, min_length=5, max_length=300)
    capacity: Optional[int] = Field(None, ge=1, le=20)
    amenities: Optional[List[str]] = None
    is_active: Optional[bool] = None


# ==================== Listing Response ====================

class ListingImageBrief(BaseModel):
    """Краткая информация о фотографии для списков"""
    id: int
    image_url: str
    is_primary: bool

    model_config = ConfigDict(from_attributes=True)


class ListingResponse(BaseModel):
    """Схема ответа с данными жилья"""
    id: int
    host_id: int
    title: str
    description: str
    city: str
    address: str
    capacity: int
    amenities: Optional[List[str]] = []
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    images: Optional[List[ListingImageBrief]] = []

    model_config = ConfigDict(from_attributes=True)

    @field_validator("amenities", mode="before")
    @classmethod
    def parse_amenities(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                # Fallback: split by comma
                return [item.strip() for item in v.split(",") if item.strip()]
        return v if isinstance(v, list) else []


class ListingBrief(BaseModel):
    """Краткая информация о жилье для списков"""
    id: int
    title: str
    city: str
    capacity: int
    is_active: bool
    primary_image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ==================== Search Filters ====================

class ListingSearchFilters(BaseModel):
    """Фильтры для поиска жилья"""
    city: Optional[str] = Field(None, description="Город (частичное совпадение)")
    check_in: Optional[date] = Field(None, description="Дата заезда")
    check_out: Optional[date] = Field(None, description="Дата выезда")
    min_capacity: Optional[int] = Field(None, ge=1, description="Минимальная вместимость")
    max_price: Optional[int] = Field(None, ge=0, description="Максимальная цена (если будет)")
    
    # Пагинация
    page: int = 1
    size: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size

    def validate_dates(self) -> bool:
        """Проверка корректности дат"""
        if self.check_in and self.check_out:
            return self.check_in < self.check_out
        return True
