"""
Common Schemas - Общие Pydantic модели
"""
from datetime import datetime
from typing import Optional, Generic, TypeVar
from pydantic import BaseModel, ConfigDict

DataT = TypeVar("DataT")


class BaseResponse(BaseModel, Generic[DataT]):
    """Базовая схема ответа API"""
    success: bool = True
    data: Optional[DataT] = None
    message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """Схема ошибки API"""
    success: bool = False
    error: str
    detail: Optional[str] = None
    status_code: int


class PaginationParams(BaseModel):
    """Параметры пагинации"""
    page: int = 1
    size: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


class PaginatedResponse(BaseModel, Generic[DataT]):
    """Ответ с пагинацией"""
    items: list[DataT]
    total: int
    page: int
    size: int
    pages: int

    @classmethod
    def create(cls, items: list[DataT], total: int, page: int, size: int) -> "PaginatedResponse[DataT]":
        """Фабричный метод для создания пагинированного ответа"""
        pages = (total + size - 1) // size if size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
