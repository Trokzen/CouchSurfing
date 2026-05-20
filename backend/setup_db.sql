-- CouchSurfing Database Setup Script
-- Для локальной PostgreSQL с паролем 123

-- 1. Создаем базу данных (если не существует)
-- Внимание: Этот запрос нужно запускать отдельно от других, 
-- так как CREATE DATABASE нельзя выполнять внутри транзакции
SELECT 'CREATE DATABASE couchsurfing' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'couchsurfing')\gexec

-- 2. Создаем пользователя (если не существует)
-- В данном случае используем стандартного postgres пользователя с паролем 123
ALTER USER postgres WITH PASSWORD '123';

-- 3. Предоставляем права на базу данных
GRANT ALL PRIVILEGES ON DATABASE couchsurfing TO postgres;

-- Инструкция по использованию:
-- 1. Подключитесь к PostgreSQL как суперпользователь (обычно postgres)
-- 2. Выполните этот скрипт
-- 3. После этого можете запускать миграции Alembic:
--    cd backend
--    alembic upgrade head
