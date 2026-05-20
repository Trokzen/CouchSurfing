"""
Auth Service - Бизнес-логика аутентификации
"""
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User
from app.schemas.auth import UserRegister, UserRole, VerificationStatus
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.exceptions import (
    AuthenticationException,
    ValidationException,
    ConflictException,
)


class AuthService:
    """Сервис для управления аутентификацией"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def register(self, user_data: UserRegister) -> User:
        """
        Регистрация нового пользователя
        
        :param user_data: Данные регистрации
        :return: Созданный пользователь
        :raises ConflictException: Если email уже занят
        """
        # Проверка на существование пользователя с таким email
        existing_user = await self.get_user_by_email(user_data.email)
        if existing_user:
            raise ConflictException("User with this email already exists")

        # Хеширование пароля
        password_hash = get_password_hash(user_data.password)

        # Создание пользователя
        user = User(
            email=user_data.email,
            password_hash=password_hash,
            full_name=user_data.full_name,
            role=user_data.role,
            verification_status=VerificationStatus.unverified,
        )

        self.session.add(user)
        await self.session.flush()  # Получаем ID
        await self.session.refresh(user)

        return user

    async def login(self, email: str, password: str) -> dict:
        """
        Вход пользователя
        
        :param email: Email пользователя
        :param password: Пароль
        :return: Словарь с токенами и данными пользователя
        :raises AuthenticationException: Если неверные учётные данные
        """
        user = await self.get_user_by_email(email)
        
        if not user:
            raise AuthenticationException("Invalid email or password")

        if not verify_password(password, user.password_hash):
            raise AuthenticationException("Invalid email or password")

        # Генерация токенов
        access_token = create_access_token(
            subject=user.id,
            role=user.role,
        )
        refresh_token = create_refresh_token(subject=user.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user,
        }

    async def refresh_tokens(self, refresh_token: str) -> dict:
        """
        Обновление токенов по refresh токену
        
        :param refresh_token: Refresh токен
        :return: Новые токены
        :raises AuthenticationException: Если токен невалиден
        """
        try:
            payload = decode_token(refresh_token)
        except Exception as e:
            raise AuthenticationException(f"Invalid refresh token: {str(e)}")

        # Проверка типа токена
        if payload.type != "refresh":
            raise AuthenticationException("Invalid token type")

        # Получение пользователя
        user_id = int(payload.sub)
        user = await self.get_user_by_id(user_id)
        
        if not user:
            raise AuthenticationException("User not found")

        # Генерация новых токенов
        new_access_token = create_access_token(
            subject=user.id,
            role=user.role,
        )
        new_refresh_token = create_refresh_token(subject=user.id)

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID"""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Получение пользователя по email"""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def change_password(
        self, 
        user_id: int, 
        old_password: str, 
        new_password: str
    ) -> bool:
        """
        Смена пароля пользователя
        
        :param user_id: ID пользователя
        :param old_password: Текущий пароль
        :param new_password: Новый пароль
        :return: True если успешно
        :raises AuthenticationException: Если неверный старый пароль
        :raises ValidationException: Если новый пароль слишком слабый
        """
        user = await self.get_user_by_id(user_id)
        
        if not user:
            raise AuthenticationException("User not found")

        # Проверка старого пароля
        if not verify_password(old_password, user.password_hash):
            raise AuthenticationException("Invalid current password")

        # Валидация нового пароля
        if len(new_password) < 8:
            raise ValidationException("Password must be at least 8 characters long")

        # Обновление пароля
        user.password_hash = get_password_hash(new_password)
        await self.session.commit()
        await self.session.refresh(user)

        return True

    async def update_verification_status(
        self, 
        user_id: int, 
        status: VerificationStatus
    ) -> User:
        """
        Обновление статуса верификации (для модераторов)
        
        :param user_id: ID пользователя
        :param status: Новый статус верификации
        :return: Обновлённый пользователь
        """
        user = await self.get_user_by_id(user_id)
        
        if not user:
            raise ValidationException("User not found")

        user.verification_status = status
        await self.session.commit()
        await self.session.refresh(user)

        return user
