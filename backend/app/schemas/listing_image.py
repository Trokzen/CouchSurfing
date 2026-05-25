"""
Listing Image Schemas - Pydantic модели для фотографий жилья
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator


# ==================== ListingImage Create/Update ====================

class ListingImageCreate(BaseModel):
    """Схема создания фотографии жилья"""
    image_url: str = Field(..., min_length=1, max_length=500)
    is_primary: bool = False

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "image_url": "/uploads/listings/abc123.jpg",
                "is_primary": True
            }
        }
    )


class ListingImageUpdate(BaseModel):
    """Схема обновления фотографии жилья"""
    is_primary: Optional[bool] = None


# ==================== ListingImage Response ====================

class ListingImageResponse(BaseModel):
    """Схема ответа с данными фотографии"""
    id: int
    listing_id: int
    image_url: str
    is_primary: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== Updated Listing Schemas with Images ====================

class ListingResponseWithImages(BaseModel):
    """Схема ответа с данными жилья и фотографиями"""
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
    images: Optional[List[ListingImageResponse]] = []

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
                return [item.strip() for item in v.split(",") if item.strip()]
        return v if isinstance(v, list) else []
