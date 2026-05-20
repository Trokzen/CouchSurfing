# ШАГ 3: Auth Module - Реализовано ✅

## Обзор

Модуль аутентификации и авторизации полностью реализован со следующими компонентами:

### 📁 Структура файлов

```
backend/app/
├── schemas/
│   └── auth.py              # Pydantic схемы (UserRegister, UserLogin, Token, UserResponse)
├── crud/
│   └── user.py              # CRUD операции для пользователей
├── services/
│   └── auth.py              # Бизнес-логика (хеширование, JWT токены)
├── routers/
│   └── auth.py              # API эндпоинты
└── core/
    ├── config.py            # Настройки (добавлен settings instance)
    └── exceptions.py        # Кастомные исключения (EmailAlreadyExistsError и др.)
```

### 🔐 Функциональность

#### 1. Регистрация (`POST /api/v1/auth/register`)
- Валидация email, пароля (мин. 8 символов), имени
- Хеширование пароля через bcrypt
- Автоматическая роль: `guest`, статус: `unverified`
- Проверка на дубликат email

#### 2. Логин (`POST /api/v1/auth/login`)
- OAuth2 формат (username=email, password)
- Возврат пары токенов: access + refresh
- Access токен: 30 минут
- Refresh токен: 7 дней

#### 3. Обновление токена (`POST /api/v1/auth/refresh`)
- Принимает refresh токен
- Возвращает новую пару токенов
- Валидация типа токена

#### 4. Профиль пользователя
- `GET /api/v1/auth/me` - получить текущий профиль
- `PUT /api/v1/auth/me` - обновить профиль
- `POST /api/v1/auth/change-password` - смена пароля

### 🛡️ Безопасность

- **JWT токены**: python-jose с алгоритмом HS256
- **Хеширование**: passlib + bcrypt
- **Dependency injection**: `get_current_user` для защищённых роутов
- **Ролевая проверка**: `require_role()` factory для проверки ролей
- **CORS**: настроен только для `http://localhost:5173`

### 📋 Pydantic схемы

| Схема | Описание |
|-------|----------|
| `UserRegister` | Регистрация (email, password, full_name, role) |
| `UserLogin` | Логин (email, password) |
| `Token` | Ответ с токенами (access_token, refresh_token) |
| `TokenPayload` | decoded JWT payload (sub, exp, type, role) |
| `UserResponse` | Данные пользователя (без пароля) |
| `UserUpdate` | Обновление профиля |
| `PasswordChange` | Смена пароля |

### 🔄 JWT Claims

```python
{
    "sub": "user_id",      # ID пользователя (string)
    "exp": 1234567890,     # Время истечения (timestamp)
    "type": "access",      # или "refresh"
    "role": "guest"        # guest/host/moderator
}
```

### 🧪 Тестирование

Все компоненты протестированы:
```
✓ Схемы аутентификации работают
✓ Хеширование паролей работает
✓ Создание JWT токенов работает
✓ Декодирование токенов работает
```

### 📡 API Endpoints

| Метод | Путь | Описание | Auth |
|-------|------|----------|------|
| POST | `/api/v1/auth/register` | Регистрация нового пользователя | ❌ |
| POST | `/api/v1/auth/login` | Вход, получение токенов | ❌ |
| POST | `/api/v1/auth/refresh` | Обновление токенов | ❌ |
| GET | `/api/v1/auth/me` | Текущий пользователь | ✅ |
| PUT | `/api/v1/auth/me` | Обновить профиль | ✅ |
| POST | `/api/v1/auth/change-password` | Сменить пароль | ✅ |

### ⚙️ Конфигурация (.env)

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/couchsurfing

# JWT
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
FRONTEND_URL=http://localhost:5173

# App
DEBUG=true
```

### 🚀 Запуск сервера

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Swagger UI доступен по адресу: http://localhost:8000/docs

---

## Готов к ШАГУ 4 (Listings и Search)
