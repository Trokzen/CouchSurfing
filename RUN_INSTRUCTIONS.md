# CouchSurfing - Инструкция по запуску

## Требования

### Backend
- Python 3.10+
- PostgreSQL 12+
- pip

### Frontend
- Node.js 18+
- npm или pnpm

## Установка и запуск

### 1. Настройка базы данных

#### Вариант A: Использование скрипта setup_db.sql

1. Подключитесь к PostgreSQL как суперпользователь (обычно postgres):
```bash
psql -U postgres -h localhost
```

2. Выполните скрипт создания БД:
```sql
\i /workspace/backend/setup_db.sql
```

Или из командной строки:
```bash
psql -U postgres -h localhost -f /workspace/backend/setup_db.sql
```

#### Вариант B: Ручное создание

```sql
CREATE DATABASE couchsurfing;
ALTER USER postgres WITH PASSWORD '123';
GRANT ALL PRIVILEGES ON DATABASE couchsurfing TO postgres;
```

### 2. Запуск миграций Alembic

```bash
cd /workspace/backend

# Применить все миграции
alembic upgrade head

# Проверить статус миграций
alembic current
```

### 3. Запуск Backend

```bash
cd /workspace/backend

# Установить зависимости (если еще не установлены)
pip install fastapi uvicorn sqlalchemy[asyncio] asyncpg pydantic pydantic-settings python-jose passlib bcrypt structlog alembic

# Запустить сервер разработки
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend будет доступен по адресу: http://localhost:8000

Swagger документация: http://localhost:8000/docs
ReDoc документация: http://localhost:8000/redoc

### 4. Запуск Frontend

```bash
cd /workspace/frontend

# Установить зависимости
npm install

# Запустить сервер разработки
npm run dev
```

Frontend будет доступен по адресу: http://localhost:5173

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Регистрация нового пользователя
- `POST /api/v1/auth/login` - Вход (OAuth2, возвращает токены)
- `GET /api/v1/auth/me` - Получить текущий профиль
- `PUT /api/v1/auth/me` - Обновить профиль
- `POST /api/v1/auth/change-password` - Изменить пароль

### Listings
- `POST /api/v1/listings/` - Создать объявление (только host)
- `GET /api/v1/listings/search` - Поиск жилья с фильтрами
- `GET /api/v1/listings/{id}` - Получить детали жилья
- `PUT /api/v1/listings/{id}` - Обновить жилье
- `DELETE /api/v1/listings/{id}` - Удалить жилье
- `GET /api/v1/listings/{id}/availability` - Проверить доступность дат

### Bookings
- `POST /api/v1/bookings/` - Создать бронирование
- `GET /api/v1/bookings/my` - Мои бронирования (как гость)
- `GET /api/v1/bookings/host` - Бронирования моего жилья (как хост)
- `GET /api/v1/bookings/{id}` - Детали бронирования
- `POST /api/v1/bookings/{id}/confirm` - Подтвердить (хост)
- `POST /api/v1/bookings/{id}/reject` - Отклонить (хост)
- `POST /api/v1/bookings/{id}/cancel` - Отменить (гость)
- `POST /api/v1/bookings/{id}/complete` - Завершить (хост)
- `GET /api/v1/bookings/{id}/status-transitions` - Доступные переходы статуса

### Reviews
- `POST /api/v1/reviews/` - Создать отзыв
- `GET /api/v1/reviews/user/{user_id}` - Отзывы и рейтинг пользователя
- `GET /api/v1/reviews/{id}` - Получить отзыв
- `POST /api/v1/reviews/{id}/hide` - Скрыть отзыв (модератор)
- `POST /api/v1/reviews/{id}/show` - Показать отзыв (модератор)
- `GET /api/v1/reviews/booking/{booking_id}/can-review` - Проверить возможность оставить отзыв

## State Machine для бронирований

```
new → pending → confirmed → completed
                ↓
            rejected
            
pending/confirmed → cancelled
```

### Переходы статусов:
- **new** → **pending**: Автоматически при создании бронирования
- **pending** → **confirmed**: Хост подтверждает бронирование
- **pending** → **rejected**: Хост отклоняет бронирование
- **pending** → **cancelled**: Гость отменяет бронирование
- **confirmed** → **cancelled**: Гость отменяет подтвержденное бронирование
- **confirmed** → **completed**: Хост завершает бронирование (после выезда)

### Важные правила:
1. Нельзя забронировать занятые даты (проверка пересечения интервалов)
2. Отзыв можно оставить только после статуса **completed**
3. Только модератор может изменять любые статусы без ограничений

## Тестирование

### Создание тестовых данных через API

1. Зарегистрировать хоста:
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "host@test.com", "password": "password123", "full_name": "Test Host", "role": "host"}'
```

2. Зарегистрировать гостя:
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "guest@test.com", "password": "password123", "full_name": "Test Guest", "role": "guest"}'
```

3. Войти как хост и получить токен:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=host@test.com&password=password123"
```

4. Создать жилье (используя полученный access_token):
```bash
curl -X POST http://localhost:8000/api/v1/listings/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"title": "Cozy Apartment", "description": "Nice place in the city center", "city": "Moscow", "address": "Tverskaya st., 1", "capacity": 2}'
```

## Конфигурация

Основная конфигурация находится в `/workspace/backend/app/core/config.py`:

- `DATABASE_URL`: postgresql+asyncpg://postgres:123@localhost:5432/couchsurfing
- `SECRET_KEY`: your-secret-key-change-in-production
- `FRONTEND_URL`: http://localhost:5173
- `DEBUG`: true

## Возможные проблемы

### Ошибка подключения к БД
Убедитесь что PostgreSQL запущен и пароль правильный:
```bash
psql -U postgres -h localhost -c "\l"
```

### Ошибка CORS
Проверьте что FRONTEND_URL в config.py совпадает с адресом frontend сервера.

### Ошибка миграций
Сбросьте базу данных и примените миграции заново:
```bash
psql -U postgres -h localhost -c "DROP DATABASE IF EXISTS couchsurfing;"
psql -U postgres -h localhost -c "CREATE DATABASE couchsurfing;"
alembic upgrade head
```
