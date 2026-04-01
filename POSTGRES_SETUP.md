# Подключение PostgreSQL к RoadMate

## Способ 1: Docker Compose (рекомендуется)

### Шаг 1: Запустить PostgreSQL

```bash
docker-compose up -d db
```

Это запустит PostgreSQL на порту `5432`.

### Шаг 2: Проверить подключение

```bash
docker-compose ps
```

Должен быть статус `Up`.

### Шаг 3: Запустить backend

```bash
docker-compose up backend
```

## Способ 2: Локальный PostgreSQL без Docker

### Установка PostgreSQL

**Windows:**
1. Скачайте с https://www.postgresql.org/download/windows/
2. Установите, запомните пароль пользователя `postgres`

**Mac:**
```bash
brew install postgresql
brew services start postgresql
```

**Linux (Ubuntu):**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### Создание БД и пользователя

```bash
# Подключиться к PostgreSQL
psql -U postgres

# Создать пользователя и БД
CREATE USER roadmate WITH PASSWORD 'roadmate_pass';
CREATE DATABASE roadmate_db OWNER roadmate;
GRANT ALL PRIVILEGES ON DATABASE roadmate_db TO roadmate;

# Выйти
\q
```

### Настройка подключения

Создайте файл `.env` в корне проекта:

```env
# Database
DATABASE_URL=postgresql+asyncpg://roadmate:roadmate_pass@localhost:5432/roadmate_db
DATABASE_URL_SYNC=postgresql://roadmate:roadmate_pass@localhost:5432/roadmate_db
DATABASE_ECHO=false

# Security
SECRET_KEY=your_super_secret_key_change_this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]

# App
DEBUG=true
APP_ENVIRONMENT=dev
```

### Запуск backend

```bash
# Установить зависимости
pip install -e .

# Запустить сервер
uvicorn app.main:app --reload
```

## Проверка подключения

После запуска откройте в браузере:
- http://localhost:8000 — корневой эндпоинт
- http://localhost:8000/docs — Swagger документация
- http://localhost:8000/health — проверка здоровья

## Устранение проблем

### PostgreSQL не запускается
```bash
# Проверить статус
docker-compose logs db

# Перезапустить
docker-compose restart db
```

### Ошибка подключения к БД
Проверьте что DATABASE_URL в `.env` совпадает с настройками в `docker-compose.yml`.

### Порт занят
```bash
# На Windows
netstat -ano | findstr :5432

# На Mac/Linux  
lsof -i :5432
```

Измените порт в `docker-compose.yml` если нужно.