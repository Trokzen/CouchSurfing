"""
Auth Router - эндпоинты для аутентификации и управления профилем.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud.user import UserCRUD
from app.services.auth import AuthService
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    Token,
    UserResponse,
    UserUpdate,
    PasswordChange,
)
from app.core.exceptions import (
    EmailAlreadyExistsError,
    UserNotFoundError,
    InvalidCredentialsError,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# OAuth2 схема для получения токена из заголовка
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """
    Dependency для получения текущего пользователя из токена.
    
    Args:
        token: JWT токен из заголовка Authorization
        db: Сессия базы данных
        
    Returns:
        Пользователь из БД
        
    Raises:
        HTTPException: Если токен невалиден или пользователь не найден
    """
    payload = AuthService.decode_token(token)
    user_crud = UserCRUD(db)
    user = await user_crud.get_by_id(int(payload.sub))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def require_role(required_role: str):
    """
    Factory для создания dependency проверки роли.
    
    Args:
        required_role: Требуемая роль ('guest', 'host', 'moderator')
        
    Returns:
        Dependency функция для проверки роли
    """
    async def role_checker(
        current_user: UserResponse = Depends(get_current_user)
    ):
        # Приводим enum к строке для сравнения
        if current_user.role.value != required_role and required_role != "any":
            # Для модератора доступен доступ всем ролям кроме moderator
            if not (required_role == "moderator" and current_user.role.value == "moderator"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Required role: {required_role}",
                )
        return current_user
    
    return role_checker


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """
    Регистрация нового пользователя.
    
    Создает аккаунт с хешированным паролем и возвращает данные пользователя.
    По умолчанию присваивается роль 'guest' и статус 'unverified'.
    """
    user_crud = UserCRUD(db)
    
    # Проверка на существующий email
    existing_user = await user_crud.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Хеширование пароля
    password_hash = AuthService.get_password_hash(user_data.password)
    
    user = await user_crud.create(user_data, password_hash)
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Вход в систему.
    
    Принимает email и пароль в формате OAuth2 (username=email).
    Возвращает пару access/refresh токенов.
    """
    user_crud = UserCRUD(db)
    
    # Аутентификация
    user = await AuthService.authenticate_user(
        email=form_data.username,
        password=form_data.password,
        user_crud=user_crud
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Создание токенов
    access_token, refresh_token = AuthService.create_token_pair(
        user_id=user.id,
        role=user.role
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Обновление access токена.
    
    Принимает refresh токен и возвращает новую пару токенов.
    """
    try:
        payload = AuthService.decode_token(refresh_token)
        
        # Проверка что это refresh токен
        if payload.type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Проверка существования пользователя
        user_crud = UserCRUD(db)
        user = await user_crud.get_by_id(int(payload.sub))
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Создание новых токенов
        new_access_token, new_refresh_token = AuthService.create_token_pair(
            user_id=user.id,
            role=user.role
        )
        
        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Получить информацию о текущем пользователе.
    
    Требует валидный access токен в заголовке Authorization.
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_profile(
    update_data: UserUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Обновить профиль пользователя.
    
    Можно изменить имя и (для модераторов) статус верификации.
    """
    user_crud = UserCRUD(db)
    
    # Только модератор может менять verification_status
    if update_data.verification_status and current_user.role.value != "moderator":
        update_data.verification_status = None
    
    updated_user = await user_crud.update(
        user_id=current_user.id,
        update_data=update_data
    )
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return updated_user


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Изменить пароль.
    
    Требует старый пароль и новый пароль (минимум 8 символов).
    """
    user_crud = UserCRUD(db)
    user = await user_crud.get_by_id(current_user.id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Проверка старого пароля
    if not AuthService.verify_password(
        password_data.old_password, 
        user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password is incorrect",
        )
    
    # Хеширование и сохранение нового пароля
    new_password_hash = AuthService.get_password_hash(password_data.new_password)
    user.password_hash = new_password_hash
    
    await db.commit()
    await db.refresh(user)
    
    return {"message": "Password changed successfully"}
