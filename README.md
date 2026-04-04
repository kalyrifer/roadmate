# RoadMate

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

cd frontend

npm run dev

BlaBlaCar clone — сервис для поиска попутчиков и организации совместных поездок.

## Содержание

- [Технологический стек](#технологический-стек)
- [Требования](#требования)
- [Быстрый старт](#быстрый-старт)
- [Настройка окружения](#настройка-окружения)
- [Запуск с Docker](#запуск-с-docker)
- [Запуск без Docker](#запуск-без-docker)
- [Миграции базы данных](#миграции-базы-данных)
- [API документация](#api-документация)
- [Структура проекта](#структура-проекта)
- [Полезные команды](#полезные-команды)

## Технологический стек

### Backend
- **Python** 3.11+
- **FastAPI** — веб-фреймворк
- **SQLAlchemy** 2.0+ — ORM (async)
- **PostgreSQL** — база данных
- **Alembic** — миграции БД
- **Pydantic** — валидация данных
- **Uvicorn** — ASGI сервер

### Frontend
- **React** 18+ — UI фреймворк
- **Vite** — сборщик
- **TypeScript** — типизация
- **React Router** — маршрутизация
- **TanStack React Query** — управление состоянием сервера
- **Zustand** — управление состоянием
- **Leaflet** — карты

### DevOps
- **Docker** + **Docker Compose** — контейнеризация

## Требования

- Docker и Docker Compose
- Python 3.11+ (для локальной разработки)
- Node.js 18+ (для локальной разработки)
- PostgreSQL (или Docker)

## Быстрый старт

Самый простой способ запустить проект — использовать Docker Compose:

```bash
# 1. Клонировать репозиторий
git clone <repository-url>
cd RoadMate

# 2. Создать .env файл
copy .env.example .env

# 3. Запустить все сервисы
docker-compose up -d

# 4. Открыть в браузере
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Настройка окружения

### Переменные окружения

Скопируйте файл `.env.example` в `.env` и настройте под ваше окружение:

```bash
copy .env.example .env
```

Основные переменные:

| Переменная | Описание | Значение по умолчанию |
|-------------|-----------|----------------------|
| `DATABASE_URL` | URL для подключения к БД | `postgresql+asyncpg://roadmate:roadmate_pass@localhost:5432/roadmate_db` |
| `JWT_SECRET_KEY` | Секретный ключ для JWT | `CHANGE_ME_IN_PRODUCTION_USE_STRONG_SECRET_KEY` |
| `APP_ENVIRONMENT` | Режим работы | `dev` |
| `APP_DEBUG` | Режим отладки | `true` |

## Запуск с Docker

### Использование Docker Compose

```bash
# Запуск всех сервисов (база данных, backend)
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка сервисов
docker-compose down
```

### Запуск только базы данных

```bash
# Запуск PostgreSQL
docker-compose up -d db

# Проверка статуса
docker-compose ps
```

### Запуск в режиме разработки

```bash
# Запуск с пересборкой
docker-compose up -d --build

# Запуск с просмотром логов в реальном времени
docker-compose up
```

### Контейнеры

| Контейнер | Порт | Описание |
|-----------|------|-----------|
| `roadmate_db` | 5432 | PostgreSQL база данных |
| `roadmate_backend` | 8000 | FastAPI backend |

## Запуск без Docker

### Backend

#### 1. Создайте виртуальное окружение

```bash
# Создание venv
python -m venv .venv

# Активация (Windows)
.venv\Scripts\activate

# Активация (Linux/Mac)
source .venv/bin/activate
```

#### 2. Установите зависимости

```bash
pip install -e ".[dev]"
```

#### 3. Настройте переменные окружения

```bash
copy .env.example .env
# Отредактируйте .env файл
```

#### 4. Запустите PostgreSQL

```bash
# С использованием Docker
docker run -d \
  --name roadmate_db \
  -e POSTGRES_USER=roadmate \
  -e POSTGRES_PASSWORD=roadmate_pass \
  -e POSTGRES_DB=roadmate_db \
  -p 5432:5432 \
  postgres:16-alpine
```

#### 5. Примените миграции

```bash
alembic upgrade head
```

#### 6. Запустите сервер

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

#### 1. Установите зависимости

```bash
cd frontend
npm install
```

#### 2. Настройте переменные окружения

При необходимости создайте `.env` файл в директории `frontend`.

```env
VITE_API_URL=http://localhost:8000
```

#### 3. Запустите dev сервер

```bash
npm run dev
```

#### 4. Сборка для продакшена

```bash
npm run build
```

## Миграции базы данных

### Создание новой миграции

```bash
alembic revision --autogenerate -m "create_users_table"
```

### Применение миграций

```bash
# Применить все миграции
alembic upgrade head

# Применить конкретную миграцию
alembic upgrade <revision_id>

# Откатить последнюю миграцию
alembic downgrade -1
```

### Просмотр миграций

```bash
# Показать текущую ревизию
alembic current

# Показать историю миграций
alembic history
```

## API документация

После запуска backend доступны следующие ресурсы:

| Ресурс | URL | Описание |
|--------|-----|----------|
| Swagger UI | http://localhost:8000/docs | Интерактивная документация API |
| ReDoc | http://localhost:8000/redoc | Альтернативная документация |
| Health Check | http://localhost:8000/health | Проверка здоровья API |
| Root | http://localhost:8000 | Информация о приложении |

### Основные эндпоинты

| Метод | URL | Описание |
|-------|-----|----------|
| POST | /api/v1/auth/register | Регистрация пользователя |
| POST | /api/v1/auth/login | Вход в систему |
| GET | /api/v1/users/me | Получить текущего пользователя |
| GET | /api/v1/trips | Список поездок |
| POST | /api/v1/trips | Создать поездку |
| GET | /api/v1/requests | Список заявок |
| POST | /api/v1/requests | Создать заявку |
| GET | /api/v1/chat/{trip_id} | Чат поездки |

## Структура проекта

```
RoadMate/
├── app/                    # Backend приложение
│   ├── api/                # API роутеры
│   │   └── v1/            # v1 версия API
│   │       ├── auth/       # Аутентификация
│   │       ├── trips/     # Поездки
│   │       ├── requests/  # Заявки
│   │       ├── chat/       # Чат
│   │       ├── reviews/     # Отзывы
│   │       └── users/     # Пользователи
│   ├── core/               # Конфигурация, безопасность
│   ├── db/                # База данных, миграции
│   ├── models/            # SQLAlchemy модели
│   ├── repositories/      # Работа с данными
│   ├── schemas/           # Pydantic схемы
│   ├── services/         # Бизнес-логика
│   └── utils/            # Утилиты
├── frontend/              # Frontend приложение
│   ├── src/
│   │   ├── components/   # React компоненты
│   │   ├── config/      # Конфигурация
│   │   ├── hooks/      # Custom хуки
│   │   ├── pages/      # Страницы
│   │   ├── services/  # API сервисы
│   │   ├── store/     # Zustand стор
│   │   └── types/     # TypeScript типы
│   └── package.json
├── alembic.ini          # Конфигурация Alembic
├── docker-compose.yml   # Docker Compose конфиг
├── Dockerfile           # Dockerfile для backend
├── pyproject.toml      # Python зависимости
└── README.md           # Этот файл
```

## Полезные команды

### Backend

```bash
# Запуск линтера
black app/
isort app/

# Проверка типов
mypy app/

# Запуск тестов
pytest

# Запуск с coverage
pytest --cov=app
```

### Frontend

```bash
# Запуск линтера
npm run lint

# Запуск TypeScript проверки
npx tsc --noEmit
```

### Docker

```bash
# Очистка всех контейнеров и томов
docker-compose down -v

# Пересборка образов
docker-compose build --no-cache

# Вход в контейнер
docker-compose exec backend bash
docker-compose exec db psql -U postgres -d roadmate_db
```

## Устранение проблем

### База данных не запускается

Проверьте, что порт 5432 не занят другим процессом:

```bash
# Windows
netstat -ano | findstr :5432

# Linux/Mac
lsof -i :5432
```

### Ошибки миграций

Если есть проблемы с миграциями, можно сбросить БД:

```bash
# Удалить все таблицы
alembic downgrade base

# Заново применить миграции
alembic upgrade head
```

### CORS ошибки

Если frontend не может обратиться к API, проверьте настройки CORS в `.env`:

```
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

## Лицензия

MIT