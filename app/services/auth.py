"""
Сервис для управления аутентификацией.
Содержит бизнес-логику: хеширование паролей, JWT токены, валидация.
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
from jose import JWTError, jwt
import bcrypt as _bcrypt
from fastapi import HTTPException, status

from app.core.config import settings
from app.schemas.auth import TokenPayload, UserRole


class AuthService:
    """Сервис аутентификации."""

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Проверить соответствие пароля хешу.
        
        Args:
            plain_password: Пароль в открытом виде
            hashed_password: Хешированный пароль из БД
            
        Returns:
            True если пароль верный
        """
        return _bcrypt.checkpw(
            plain_password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )

    @staticmethod
    def get_password_hash(password: str) -> str:
        """
        Получить хеш пароля.
        
        Args:
            password: Пароль в открытом виде
            
        Returns:
            Хешированный пароль
        """
        return _bcrypt.hashpw(
            password.encode('utf-8'), 
            _bcrypt.gensalt()
        ).decode('utf-8')

    @staticmethod
    def create_access_token(
        subject: str, 
        role: UserRole,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Создать access токен.
        
        Args:
            subject: ID пользователя (будет в claim 'sub')
            role: Роль пользователя
            expires_delta: Время жизни токена (опционально)
            
        Returns:
            JWT токен
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode = {
            "sub": str(subject),
            "exp": expire,
            "type": "access",
            "role": role.value
        }
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def create_refresh_token(
        subject: str,
        role: UserRole,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Создать refresh токен.
        
        Args:
            subject: ID пользователя
            role: Роль пользователя
            expires_delta: Время жизни токена (опционально)
            
        Returns:
            JWT токен
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )
        
        to_encode = {
            "sub": str(subject),
            "exp": expire,
            "type": "refresh",
            "role": role.value
        }
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> TokenPayload:
        """
        Декодировать и валидировать JWT токен.
        
        Args:
            token: JWT токен
            
        Returns:
            TokenPayload с данными пользователя
            
        Raises:
            HTTPException: Если токен невалиден или истек
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            
            user_id: str = payload.get("sub")
            exp: datetime = payload.get("exp")
            token_type: str = payload.get("type")
            role: str = payload.get("role")
            
            if user_id is None or exp is None or token_type is None or role is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return TokenPayload(
                sub=user_id,
                exp=datetime.fromtimestamp(exp),
                type=token_type,
                role=UserRole(role)
            )
            
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    async def authenticate_user(
        email: str, 
        password: str,
        user_crud
    ) -> Optional[object]:
        """
        Аутентифицировать пользователя по email и паролю.
        
        Args:
            email: Email пользователя
            password: Пароль в открытом виде
            user_crud: CRUD объект для доступа к БД
            
        Returns:
            Пользователь если аутентификация успешна, иначе None
        """
        user = await user_crud.get_by_email(email)
        if not user:
            return None
        
        if not AuthService.verify_password(password, user.password_hash):
            return None
        
        return user

    @staticmethod
    def create_token_pair(user_id: int, role: UserRole) -> Tuple[str, str]:
        """
        Создать пару access/refresh токенов.
        
        Args:
            user_id: ID пользователя
            role: Роль пользователя
            
        Returns:
            Кортеж (access_token, refresh_token)
        """
        access_token = AuthService.create_access_token(
            subject=str(user_id),
            role=role
        )
        refresh_token = AuthService.create_refresh_token(
            subject=str(user_id),
            role=role
        )
        return access_token, refresh_token
