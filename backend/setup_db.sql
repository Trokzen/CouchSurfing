-- CouchSurfing Database Setup Script
-- Для локальной PostgreSQL с паролем 1234
-- Этот скрипт создает схему couchsurfing в БД postgres и все необходимые таблицы

-- ============================================================================
-- ИНСТРУКЦИЯ ПО ИЗМЕНЕНИЮ ПАРОЛЯ БД
-- ============================================================================
-- Пароль от базы данных задается в ТРЕХ местах:
-- 
-- 1. В этом файле (setup_db.sql) - строка ниже:
--    ALTER USER postgres WITH PASSWORD '1234';
--
-- 2. В файле конфигурации приложения /workspace/backend/app/core/config.py:
--    DATABASE_URL: str = "postgresql+asyncpg://postgres:1234@localhost:5432/postgres?options=-c%20search_path%3Dcouchsurfing"
--
-- 3. В файле миграций /workspace/backend/alembic.ini:
--    sqlalchemy.url = postgresql+asyncpg://postgres:1234@localhost:5432/postgres?options=-c%20search_path%3Dcouchsurfing
--
-- Чтобы сменить пароль:
--    a) Измените пароль в этом файле до запуска скрипта
--    b) Измените пароль в config.py в строке подключения DATABASE_URL
--    c) Измените пароль в alembic.ini в параметре sqlalchemy.url
--    d) Перезапустите приложение
-- ============================================================================

-- 1. Устанавливаем пароль для пользователя postgres
ALTER USER postgres WITH PASSWORD '1234';

-- ============================================================================
-- СОЗДАНИЕ СХЕМЫ И ТАБЛИЦ
-- ============================================================================

-- 2. Создаем схему couchsurfing (если не существует)
CREATE SCHEMA IF NOT EXISTS couchsurfing;

-- Переключаемся на схему couchsurfing
SET search_path TO couchsurfing;

-- Создаем ENUM типы
CREATE TYPE user_role AS ENUM ('guest', 'host', 'moderator');
CREATE TYPE verification_status AS ENUM ('unverified', 'pending', 'verified', 'rejected');
CREATE TYPE booking_status AS ENUM ('new', 'pending', 'confirmed', 'rejected', 'cancelled', 'completed');

-- Таблица пользователей (users)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role user_role DEFAULT 'guest' NOT NULL,
    verification_status verification_status DEFAULT 'unverified' NOT NULL,
    avatar_url VARCHAR(500),
    bio TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Индексы для таблицы users
CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
CREATE INDEX IF NOT EXISTS ix_users_role ON users(role);

-- Таблица размещений (listings)
CREATE TABLE IF NOT EXISTS listings (
    id SERIAL PRIMARY KEY,
    host_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    city VARCHAR(100) NOT NULL,
    address VARCHAR(500) NOT NULL,
    capacity INTEGER NOT NULL DEFAULT 1,
    price_per_night NUMERIC(10, 2),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    amenities TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Индексы для таблицы listings
CREATE INDEX IF NOT EXISTS ix_listings_host_id ON listings(host_id);
CREATE INDEX IF NOT EXISTS ix_listings_city ON listings(city);
CREATE INDEX IF NOT EXISTS ix_listings_is_active ON listings(is_active);
CREATE INDEX IF NOT EXISTS ix_listings_city_active ON listings(city, is_active);
CREATE INDEX IF NOT EXISTS ix_listings_host_active ON listings(host_id, is_active);

-- Таблица бронирований (bookings)
CREATE TABLE IF NOT EXISTS bookings (
    id SERIAL PRIMARY KEY,
    guest_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    listing_id INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    status booking_status DEFAULT 'new' NOT NULL,
    guest_message TEXT,
    host_response TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Индексы для таблицы bookings
CREATE INDEX IF NOT EXISTS ix_bookings_guest_id ON bookings(guest_id);
CREATE INDEX IF NOT EXISTS ix_bookings_listing_id ON bookings(listing_id);
CREATE INDEX IF NOT EXISTS ix_bookings_status ON bookings(status);
CREATE INDEX IF NOT EXISTS ix_bookings_dates ON bookings(start_date, end_date);
CREATE INDEX IF NOT EXISTS ix_bookings_listing_dates ON bookings(listing_id, start_date, end_date);

-- Таблица отзывов (reviews)
CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    booking_id INTEGER NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
    author_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    is_visible BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Индексы для таблицы reviews
CREATE INDEX IF NOT EXISTS ix_reviews_booking_id ON reviews(booking_id);
CREATE INDEX IF NOT EXISTS ix_reviews_author_id ON reviews(author_id);
CREATE INDEX IF NOT EXISTS ix_reviews_target_id ON reviews(target_id);
CREATE INDEX IF NOT EXISTS ix_reviews_target ON reviews(target_id, is_visible);
CREATE UNIQUE INDEX IF NOT EXISTS ix_reviews_booking_unique ON reviews(booking_id, author_id);

-- Таблица сообщений (messages)
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    receiver_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    booking_id INTEGER REFERENCES bookings(id) ON DELETE SET NULL,
    content TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Индексы для таблицы messages
CREATE INDEX IF NOT EXISTS ix_messages_sender_id ON messages(sender_id);
CREATE INDEX IF NOT EXISTS ix_messages_receiver_id ON messages(receiver_id);
CREATE INDEX IF NOT EXISTS ix_messages_booking_id ON messages(booking_id);
CREATE INDEX IF NOT EXISTS ix_messages_conversation ON messages(sender_id, receiver_id, created_at);
CREATE INDEX IF NOT EXISTS ix_messages_unread ON messages(receiver_id, is_read);

-- Триггер для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_listings_updated_at
    BEFORE UPDATE ON listings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bookings_updated_at
    BEFORE UPDATE ON bookings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ИНСТРУКЦИЯ ПО ИСПОЛЬЗОВАНИЮ
-- ============================================================================
-- 1. Запустите PostgreSQL на вашем локальном ПК
-- 2. Подключитесь к PostgreSQL как суперпользователь (обычно postgres)
--    Пример через psql: psql -U postgres
-- 3. Выполните этот скрипт: \i /workspace/backend/setup_db.sql
-- 
-- 4. После этого можете запускать приложение:
--    cd /workspace/backend
--    python -m uvicorn app.main:app --reload
-- ============================================================================
