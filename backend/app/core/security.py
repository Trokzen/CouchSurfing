"""
Security utilities - JWT, password hashing
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt as _bcrypt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.schemas.auth import TokenPayload, UserRole
from app.models import User
from app.crud.user import UserCRUD


# ==================== Password Hashing ====================


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля against хеша"""
    return _bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    """Хеширование пароля"""
    return _bcrypt.hashpw(
        password.encode('utf-8'), 
        _bcrypt.gensalt()
    ).decode('utf-8')


# ==================== JWT Token Operations ====================

security = HTTPBearer(auto_error=False)


def create_access_token(
    subject: str | int,
    role: UserRole,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Создание Access токена
    
    :param subject: ID пользователя (будет преобразован в строку)
    :param role: Роль пользователя
    :param expires_delta: Время жизни токена (по умолчанию из конфига)
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    expire = datetime.utcnow() + expires_delta
    
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "access",
        "role": role.value,
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(
    subject: str | int,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Создание Refresh токена
    
    :param subject: ID пользователя
    :param expires_delta: Время жизни токена (по умолчанию из конфига)
    """
    if expires_delta is None:
        expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    expire = datetime.utcnow() + expires_delta
    
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "refresh",
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> TokenPayload:
    """
    Декодирование и валидация JWT токена
    
    :param token: JWT токен
    :return: TokenPayload с данными пользователя
    :raises HTTPException: Если токен невалиден или истёк
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
    
        sub = payload.get("sub")
        exp = payload.get("exp")
        token_type = payload.get("type")
        role = payload.get("role")
        
        if sub is None or exp is None or token_type is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Преобразуем роль в enum если есть
        user_role = UserRole(role) if role else UserRole.GUEST
        
        return TokenPayload(
            sub=sub,
            exp=datetime.fromtimestamp(exp),
            type=token_type,
            role=user_role,
        )
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ==================== Dependencies ====================

async def get_current_user_token(
    credentials: HTTPAuthorizationCredentials | None = None
) -> TokenPayload:
    """
    Dependency для получения текущего пользователя из токена
    
    Используется в роутах для проверки авторизации.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    return decode_token(token)


async def get_current_user_id(
    token_payload: TokenPayload = get_current_user_token
) -> int:
    """
    Dependency для получения ID текущего пользователя
    
    Возвращает integer ID из токена.
    """
    return int(token_payload.sub)


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token_payload: TokenPayload = get_current_user_token
) -> User:
    """
    Dependency для получения объекта текущего пользователя из БД
    
    Возвращает полный объект User для использования в сервисах.
    """
    user_id = int(token_payload.sub)
    crud = UserCRUD(db)
    user = await crud.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def require_role(*allowed_roles: UserRole):
    """
    Factory для создания dependency проверки роли
    
    Использование:
        @router.get("/admin", dependencies=[Depends(require_role(UserRole.moderator))])
    """
    async def role_checker(
        token_payload: TokenPayload = get_current_user_token
    ) -> UserRole:
        if token_payload.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role {token_payload.role.value} is not authorized. "
                       f"Required: {[r.value for r in allowed_roles]}",
            )
        return token_payload.role
    
    return role_checker
