"""
CRUD операции для пользователей.
Инкапсулирует прямой доступ к базе данных.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError

from app.models import User
from app.schemas.auth import UserRegister, UserUpdate, UserRole, VerificationStatus


class UserCRUD:
    """Класс для CRUD операций с пользователями."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Получить пользователя по email."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, user_data: UserRegister, password_hash: str) -> User:
        """
        Создать нового пользователя.
        
        Args:
            user_data: Данные регистрации
            password_hash: Хешированный пароль
            
        Returns:
            Созданный пользователь
            
        Raises:
            IntegrityError: Если email уже существует
        """
        user = User(
            email=user_data.email,
            password_hash=password_hash,
            full_name=user_data.full_name,
            role=user_data.role,
            verification_status=VerificationStatus.unverified,
        )
        self.db.add(user)
        await self.db.flush()  # Получаем ID до коммита
        await self.db.refresh(user)
        return user

    async def update(self, user_id: int, update_data: UserUpdate) -> Optional[User]:
        """Обновить данные пользователя."""
        update_dict = update_data.model_dump(exclude_unset=True)
        if not update_dict:
            return await self.get_by_id(user_id)

        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(**update_dict, updated_at=datetime.utcnow())
        )
        await self.db.commit()
        return await self.get_by_id(user_id)

    async def delete(self, user_id: int) -> bool:
        """Удалить пользователя."""
        result = await self.db.execute(delete(User).where(User.id == user_id))
        await self.db.commit()
        return result.rowcount > 0

    async def list_users(
        self, 
        skip: int = 0, 
        limit: int = 100,
        role: Optional[UserRole] = None,
        verification_status: Optional[VerificationStatus] = None
    ) -> List[User]:
        """Получить список пользователей с фильтрацией."""
        query = select(User)
        
        if role:
            query = query.where(User.role == role)
        if verification_status:
            query = query.where(User.verification_status == verification_status)
            
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_verification_status(
        self, 
        user_id: int, 
        status: VerificationStatus
    ) -> Optional[User]:
        """Обновить статус верификации пользователя."""
        return await self.update(
            user_id, 
            UserUpdate(verification_status=status)
        )


# Экземпляр для использования (будет создан в依赖 injection)
# Используем как: crud = UserCRUD(db_session)
