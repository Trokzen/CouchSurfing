# CouchSurfing Backend - Инструкция по запуску

## Требования
- Python 3.10+
- PostgreSQL 12+
- Node.js 18+ (для фронтенда)

## 1. Настройка базы данных

### Вариант А: Автоматическая настройка (рекомендуется)

1. Установите пароль для пользователя postgres:
```bash
psql -U postgres -c "ALTER USER postgres WITH PASSWORD '123';"
```

2. Создайте базу данных:
```bash
psql -U postgres -c "CREATE DATABASE couchsurfing;"
```

Или выполните скрипт setup_db.sql:
```bash
psql -U postgres -f setup_db.sql
```

### Вариант Б: Ручная настройка через psql

```bash
# Подключитесь к PostgreSQL
psql -U postgres

# Внутри psql выполните:
ALTER USER postgres WITH PASSWORD '123';
CREATE DATABASE couchsurfing;
\q
```

## 2. Установка зависимостей Backend

```bash
cd backend

# Создайте виртуальное окружение (опционально, но рекомендуется)
python -m venv venv

# Активируйте виртуальное окружение
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Установите зависимости
pip install -r requirements.txt
```

## 3. Применение миграций

```bash
cd backend

# Примените все миграции
alembic upgrade head
```

## 4. Запуск Backend сервера

```bash
cd backend

# Запуск через uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Или через python
python -m app.main
```

Сервер будет доступен по адресу: http://localhost:8000
Swagger UI: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc

## 5. Проверка работы

1. Откройте http://localhost:8000/health
   - Должен вернуться статус: `{"status": "healthy", "version": "1.0.0"}`

2. Откройте http://localhost:8000/docs
   - Протестируйте endpoints через Swagger UI

## 6. Настройка Frontend (опционально)

```bash
cd frontend

# Установите зависимости
npm install

# Запустите development сервер
npm run dev
```

Frontend будет доступен по адресу: http://localhost:5173

## Решение проблем

### Ошибка подключения к базе данных

Убедитесь что:
1. PostgreSQL запущен
2. Пароль пользователя postgres = 123
3. База данных couchsurfing существует
4. В файле backend/app/core/config.py правильный DATABASE_URL

### Ошибка миграций

```bash
# Сбросьте миграции и примените заново
alembic downgrade base
alembic upgrade head
```

### Ошибка CORS

Убедитесь что FRONTEND_URL в config.py совпадает с адресом фронтенда (по умолчанию http://localhost:5173)
