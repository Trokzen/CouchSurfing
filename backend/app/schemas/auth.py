"""
Auth Schemas - Pydantic модели для аутентификации
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models import UserRole, VerificationStatus


# ==================== Registration ====================

class UserRegister(BaseModel):
    """Схема регистрации нового пользователя"""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Пароль минимум 8 символов")
    full_name: str = Field(..., min_length=2, max_length=100)
    role: UserRole = UserRole.GUEST

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
                "full_name": "John Doe",
                "role": "guest"
            }
        }
    )


# ==================== Login ====================

class UserLogin(BaseModel):
    """Схема входа пользователя"""
    email: EmailStr
    password: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
            }
        }
    )


# ==================== Token ====================

class Token(BaseModel):
    """Схема ответа с токенами"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Полезная нагрузка JWT токена"""
    sub: str  # user id
    exp: datetime  # expiration time
    type: str  # "access" or "refresh"
    role: UserRole


# ==================== User Response ====================

class UserResponse(BaseModel):
    """Схема ответа с данными пользователя (без пароля)"""
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    verification_status: VerificationStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """Схема обновления данных пользователя"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    verification_status: Optional[VerificationStatus] = None

    model_config = ConfigDict(from_attributes=True)


# ==================== Password Change ====================

class PasswordChange(BaseModel):
    """Схема смены пароля"""
    old_password: str
    new_password: str = Field(..., min_length=8)
