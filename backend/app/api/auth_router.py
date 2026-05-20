"""
Auth Router - API endpoints для аутентификации
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    Token,
    UserResponse,
    PasswordChange,
)
from app.services.auth_service import AuthService
from app.core.security import (
    get_current_user_id,
    get_current_user_token,
    require_role,
    UserRole,
)
from app.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя",
)
async def register(
    user_data: UserRegister,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Регистрация нового пользователя в системе.
    
    После успешной регистрации пользователь получает статус "unverified".
    """
    auth_service = AuthService(session)
    user = await auth_service.register(user_data)
    return user


@router.post(
    "/login",
    response_model=Token,
    summary="Вход в систему",
)
async def login(
    credentials: UserLogin,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Аутентификация пользователя по email и паролю.
    
    Возвращает access и refresh токены для последующих запросов.
    """
    auth_service = AuthService(session)
    result = await auth_service.login(credentials.email, credentials.password)
    return Token(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type=result["token_type"],
    )


@router.post(
    "/refresh",
    response_model=Token,
    summary="Обновление токенов",
)
async def refresh_tokens(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Обновление access и refresh токенов.
    
    Требует валидный refresh токен в теле запроса.
    """
    body = await request.json()
    refresh_token = body.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token is required",
        )
    
    auth_service = AuthService(session)
    result = await auth_service.refresh_tokens(refresh_token)
    return Token(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type=result["token_type"],
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Получение данных текущего пользователя",
)
async def get_current_user_profile(
    current_user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Получение информации о текущем авторизованном пользователе.
    
    Требует валидный access токен в заголовке Authorization.
    """
    auth_service = AuthService(session)
    user = await auth_service.get_user_by_id(current_user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return user


@router.post(
    "/change-password",
    summary="Смена пароля",
)
async def change_password(
    password_data: PasswordChange,
    current_user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Смена пароля текущего пользователя.
    
    Требуется указать текущий пароль и новый пароль (минимум 8 символов).
    """
    auth_service = AuthService(session)
    await auth_service.change_password(
        user_id=current_user_id,
        old_password=password_data.old_password,
        new_password=password_data.new_password,
    )
    
    return {"message": "Password changed successfully"}


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Получение данных пользователя по ID",
)
async def get_user_by_id(
    user_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Получение информации о пользователе по его ID.
    
    Доступно всем авторизованным пользователям.
    """
    auth_service = AuthService(session)
    user = await auth_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return user


@router.patch(
    "/{user_id}/verification",
    response_model=UserResponse,
    summary="Изменение статуса верификации (только для модераторов)",
    dependencies=[Depends(require_role(UserRole.moderator))],
)
async def update_verification_status(
    user_id: int,
    verification_status: str,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Изменение статуса верификации пользователя.
    
    Доступно только модераторам.
    Возможные статусы: unverified, pending, verified
    """
    from app.schemas.auth import VerificationStatus
    
    try:
        status_enum = VerificationStatus(verification_status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid verification status. Valid values: {[s.value for s in VerificationStatus]}",
        )
    
    auth_service = AuthService(session)
    user = await auth_service.update_verification_status(
        user_id=user_id,
        status=status_enum,
    )
    
    return user
