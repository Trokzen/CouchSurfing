"""
Message Schemas - Pydantic модели для сообщений
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# ==================== Message Create ====================

class MessageCreate(BaseModel):
    """Схема создания сообщения"""
    receiver_id: int
    booking_id: Optional[int] = Field(None, description="ID бронирования (если сообщение связано)")
    content: str = Field(..., min_length=1, max_length=2000)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "receiver_id": 15,
                "booking_id": 42,
                "content": "Hi! What time is check-in?"
            }
        }
    )


# ==================== Message Response ====================

class MessageResponse(BaseModel):
    """Схема ответа с данными сообщения"""
    id: int
    sender_id: int
    sender_name: str
    receiver_id: int
    receiver_name: str
    booking_id: Optional[int]
    content: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageBrief(BaseModel):
    """Краткая информация о сообщении для чата"""
    id: int
    sender_id: int
    content: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== Conversation ====================

class ConversationPreview(BaseModel):
    """Превью переписки с пользователем"""
    partner_id: int
    partner_name: str
    last_message: str
    last_message_at: datetime
    unread_count: int
    partner_avatar: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
