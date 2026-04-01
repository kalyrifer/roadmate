# RoadMate Backend

## Технологический стек

- **FastAPI** — HTTP API и WebSocket сервер
- **PostgreSQL** — реляционная база данных
- **SQLAlchemy 2.0** — ORM с полной типизацией и асинхронной поддержкой
- **Alembic** — управление миграциями БД
- **Pydantic v2** — валидация данных и схемы API
- **JWT** — access токены для авторизации
- **Pytest** — тестирование с fixtures для FastAPI
- **Docker Compose** — контейнеризация backend и PostgreSQL

## Архитектурные принципы

### Слои приложения

1. **API Layer** (`app/api/`) — HTTP эндпоинты и роутеры FastAPI
2. **Schemas Layer** (`app/schemas/`) — Pydantic модели для запросов/ответов
3. **Services Layer** (`app/services/`) — бизнес-логика
4. **Repositories Layer** (`app/repositories/`) — доступ к данным
5. **Models Layer** (`app/models/`) — SQLAlchemy модели БД

### Границы системы

Backend отвечает за:
- API для frontend
- Бизнес-логику (поездки, бронирования, отзывы)
- Работу с PostgreSQL
- JWT авторизацию
- WebSocket чат
- Уведомления
- Админ-панель

Frontend работает отдельно и обращается к backend через REST API.

## Доменная архитектура

### Обоснование декомпозиции на домены

В приложении типа BlaBlaCar существуют четко различимые бизнес- области, каждая из которых имеет свою специфику, набор сущностей и правил:

- **Auth** — управление аутентификацией и авторизацией
- **Users** — профили пользователей, верификация, настройки
- **Trips** — создание и управление поездками (основной домен)
- **Requests** — запросы на бронирование мест в поездках
- **Chat** — коммуникация между пользователями в реальном времени
- **Reviews** — система отзывов и рейтингов
- **Notifications** — уведомления (email, push, in-app)
- **Admin** — модерация и административные функции

Каждый домен представляет отдельный bounded context в терминах DDD. Это означает, что:

- Домены развиваются независимо друг от друга
- Изменения в одном домене минимально затрагивают другие
- Команды разработки могут работать над разными доменами параллельно
- Каждый домен имеет свою зону ответственности и четкий API

### Обоснование разделения слоев

Слоистая архитектура (Layered Architecture) применяется внутри каждого домена:

```
API → Schemas → Services → Repositories → Models
```

**Почему слои разделены:**

1. **Разделение ответственности (Separation of Concerns)** — каждый слой делает только свою работу, что упрощает понимание и поддержку кода
2. **Тестируемость** — каждый слой можно тестировать изолированно с моками зависимостей
3. **Переиспользуемость** — сервисы могут использоваться из разных API эндпоинтов, репозитории — из разных сервисов
4. **Изоляция изменений** — смена ORM, формата API или бизнес-правил затрагивает только один слой
5. **Явные зависимости** — зависимости всегда идут сверху вниз: API зависит от Schemas, Schemas от Services, Services от Repositories, Repositories от Models

**Почему сервисы не должны содержать HTTP-логику:**

- Сервисы — это слой бизнес-логики, который должен быть независим от транспортного протокола
- Один и тот же сервис может использоваться из REST API, WebSocket, GraphQL, gRPC или CLI
- Тестирование бизнес-логики упрощается без HTTP-контекста
- Изменения в HTTP-протоколе (коды ошибок, форматы заголовков) не затрагивают бизнес-логику

**Почему репозитории не должны содержать бизнес-логику:**

- Репозитории — это слой абстракции над хранилищем данных
- Они отвечают только за CRUD-операции: создание, чтение, обновление, удаление
- Бизнес-логика в репозиториях приводит к дублированию при работе с данными из разных сервисов
- Подмена хранилища (например, с PostgreSQL на MongoDB) должна затрагивать только репозитории

## Структура проекта

```
RoadMate/
├── app/
│   ├── api/                          # HTTP роутеры FastAPI
│   │   ├── deps.py                   # Зависимости API (get_db, get_current_user)
│   │   ├── websocket.py              # WebSocket эндпоинты
│   │   └── v1/                       # API v1
│   │       ├── __init__.py
│   │       ├── api_router.py         # Объединение всех роутеров v1
│   │       ├── auth/                 # Домен: Auth
│   │       │   ├── __init__.py
│   │       │   └── router.py          # /auth эндпоинты
│   │       ├── users/                # Домен: Users
│   │       │   ├── __init__.py
│   │       │   └── router.py         # /users эндпоинты
│   │       ├── trips/                # Домен: Trips
│   │       │   ├── __init__.py
│   │       │   └── router.py          # /trips эндпоинты
│   │       ├── requests/             # Домен: Requests
│   │       │   ├── __init__.py
│   │       │   └── router.py         # /requests эндпоинты
│   │       ├── chat/                 # Домен: Chat
│   │       │   ├── __init__.py
│   │       │   └── router.py         # /chat эндпоинты
│   │       ├── reviews/              # Домен: Reviews
│   │       │   ├── __init__.py
│   │       │   └── router.py         # /reviews эндпоинты
│   │       ├── notifications/        # Домен: Notifications
│   │       │   ├── __init__.py
│   │       │   └── router.py         # /notifications эндпоинты
│   │       └── admin/                # Домен: Admin
│   │           ├── __init__.py
│   │           └── router.py         # /admin эндпоинты
│   │
│   ├── core/                         # Конфигурация и безопасность
│   │   ├── __init__.py
│   │   ├── config.py                 # Настройки приложения (Pydantic Settings)
│   │   ├── security.py               # JWT, хеширование паролей, токены
│   │   ├── logging.py                # Логирование
│   │   ├── exceptions.py             # Кастомные исключения
│   │   └── constants.py              # Константы приложения
│   │
│   ├── db/                          # Подключение к БД
│   │   ├── __init__.py
│   │   ├── base.py                   # Базовые классы SQLAlchemy (Base, Timestamp)
│   │   ├── session.py                # Сессия БД (AsyncSession)
│   │   └── migration/                # Alembic миграции
│   │       ├── env.py
│   │       ├── script.py.mako
│   │       └── versions/
│   │
│   ├── models/                      # SQLAlchemy модели БД (доменная организация)
│   │   ├── __init__.py
│   │   ├── auth/                     # Модели домена Auth
│   │   │   ├── __init__.py
│   │   │   ├── token.py              # Token (JWT токены)
│   │   │   └── password_reset.py     # PasswordReset (сброс пароля)
│   │   ├── users/                    # Модели домена Users
│   │   │   ├── __init__.py
│   │   │   ├── user.py               # User (основная модель пользователя)
│   │   │   ├── user_profile.py       # UserProfile (профиль, аватар)
│   │   │   ├── user_verification.py  # UserVerification (верификация)
│   │   │   └── user_preferences.py   # UserPreferences (настройки)
│   │   ├── trips/                    # Модели домена Trips
│   │   │   ├── __init__.py
│   │   │   ├── trip.py               # Trip (поездка)
│   │   │   ├── trip_point.py         # TripPoint (точка маршрута)
│   │   │   ├── trip_seat.py          # TripSeat (место в поездке)
│   │   │   └── car.py                # Car (транспортное средство)
│   │   ├── requests/                 # Модели домена Requests
│   │   │   ├── __init__.py
│   │   │   ├── trip_request.py       # TripRequest (запрос на бронирование)
│   │   │   └── request_status.py     # RequestStatus (история статусов)
│   │   ├── chat/                     # Модели домена Chat
│   │   │   ├── __init__.py
│   │   │   ├── conversation.py       # Conversation (беседа)
│   │   │   ├── message.py            # Message (сообщение)
│   │   │   └── message_read.py       # MessageRead (прочтение)
│   │   ├── reviews/                  # Модели домена Reviews
│   │   │   ├── __init__.py
│   │   │   ├── review.py             # Review (отзыв)
│   │   │   └── review_rating.py      # ReviewRating (оценка)
│   │   ├── notifications/            # Модели домена Notifications
│   │   │   ├── __init__.py
│   │   │   ├── notification.py       # Notification (уведомление)
│   │   │   ├── notification_channel.py # NotificationChannel (канал)
│   │   │   └── notification_template.py # NotificationTemplate (шаблон)
│   │   └── admin/                    # Модели домена Admin
│   │       ├── __init__.py
│   │       ├── admin_user.py         # AdminUser (администратор)
│   │       ├── audit_log.py         # AuditLog (журнал действий)
│   │       └── moderation.py        # Moderation (модерация)
│   │
│   ├── schemas/                      # Pydantic схемы (доменная организация)
│   │   ├── __init__.py
│   │   ├── base.py                   # Базовые схемы (Response, Pagination)
│   │   ├── auth/                     # Схемы домена Auth
│   │   │   ├── __init__.py
│   │   │   ├── token.py              # Схемы токенов
│   │   │   ├── login.py              # Схемы входа
│   │   │   └── password_reset.py    # Схемы сброса пароля
│   │   ├── users/                    # Схемы домена Users
│   │   │   ├── __init__.py
│   │   │   ├── user.py               # Схемы пользователя
│   │   │   ├── profile.py            # Схемы профиля
│   │   │   └── preferences.py        # Схемы настроек
│   │   ├── trips/                    # Схемы домена Trips
│   │   │   ├── __init__.py
│   │   │   ├── trip.py               # Схемы поездки
│   │   │   ├── trip_point.py         # Схемы точки маршрута
│   │   │   ├── trip_seat.py          # Схемы места
│   │   │   └── car.py                # Схемы автомобиля
│   │   ├── requests/                 # Схемы домена Requests
│   │   │   ├── __init__.py
│   │   │   ├── trip_request.py       # Схемы запроса на бронирование
│   │   │   └── request_status.py     # Схемы статуса запроса
│   │   ├── chat/                     # Схемы домена Chat
│   │   │   ├── __init__.py
│   │   │   ├── conversation.py       # Схемы беседы
│   │   │   ├── message.py            # Схемы сообщения
│   │   │   └── websocket.py         # Схемы для WebSocket
│   │   ├── reviews/                  # Схемы домена Reviews
│   │   │   ├── __init__.py
│   │   │   ├── review.py             # Схемы отзыва
│   │   │   └── review_rating.py      # Схемы рейтинга
│   │   ├── notifications/            # Схемы домена Notifications
│   │   │   ├── __init__.py
│   │   │   ├── notification.py       # Схемы уведомления
│   │   │   └── notification_create.py # Схемы создания
│   │   └── admin/                    # Схемы домена Admin
│   │       ├── __init__.py
│   │       ├── admin_user.py        # Схемы администратора
│   │       ├── audit_log.py         # Схемы журнала
│   │       └── moderation.py        # Схемы модерации
│   │
│   ├── services/                     # Бизнес-логика (доменная организация)
│   │   ├── __init__.py
│   │   ├── auth/                     # Сервисы домена Auth
│   │   │   ├── __init__.py
│   │   │   ├── authentication.py     # Аутентификация (verify_password, create_token)
│   │   │   ├── password_service.py  # Управление паролями
│   │   │   └── token_service.py      # Работа с токенами
│   │   ├── users/                    # Сервисы домена Users
│   │   │   ├── __init__.py
│   │   │   ├── user_service.py      # Управление пользователями
│   │   │   ├── profile_service.py    # Управление профилем
│   │   │   ├── verification_service.py # Верификация пользователей
│   │   │   └── preferences_service.py # Управление настройками
│   │   ├── trips/                    # Сервисы домена Trips
│   │   │   ├── __init__.py
│   │   │   ├── trip_service.py      # Управление поездками
│   │   │   ├── trip_search_service.py # Поиск поездок
│   │   │   ├── trip_point_service.py # Управление точками маршрута
│   │   │   ├── seat_service.py      # Управление местами
│   │   │   └── car_service.py        # Управление автомобилями
│   │   ├── requests/                 # Сервисы домена Requests
│   │   │   ├── __init__.py
│   │   │   ├── request_service.py   # Управление запросами
│   │   │   ├── request_approval_service.py # Одобрение/отклонение
│   │   │   └── request_notification_service.py # Уведомления о статусе
│   │   ├── chat/                     # Сервисы домена Chat
│   │   │   ├── __init__.py
│   │   │   ├── conversation_service.py # Управление беседами
│   │   │   ├── message_service.py    # Управление сообщениями
│   │   │   ├── unread_service.py     # Счетчик непрочитанных
│   │   │   └── websocket_service.py  # WebSocket коммуникация
│   │   ├── reviews/                  # Сервисы домена Reviews
│   │   │   ├── __init__.py
│   │   │   ├── review_service.py     # Управление отзывами
│   │   │   ├── rating_service.py     # Управление рейтингами
│   │   │   └── review_aggregation_service.py # Агрегация рейтингов
│   │   ├── notifications/            # Сервисы домена Notifications
│   │   │   ├── __init__.py
│   │   │   ├── notification_service.py # Отправка уведомлений
│   │   │   ├── email_service.py      # Email уведомления
│   │   │   ├── push_service.py       # Push уведомления
│   │   │   └── template_service.py   # Управление шаблонами
│   │   └── admin/                    # Сервисы домена Admin
│   │       ├── __init__.py
│   │       ├── admin_auth_service.py # Аутентификация админов
│   │       ├── moderation_service.py # Модерация контента
│   │       ├── audit_service.py      # Управление аудитом
│   │       └── stats_service.py      # Статистика и аналитика
│   │
│   ├── repositories/                 # Доступ к данным (доменная организация)
│   │   ├── __init__.py
│   │   ├── auth/                     # Репозитории домена Auth
│   │   │   ├── __init__.py
│   │   │   └── token_repository.py  # Работа с токенами
│   │   ├── users/                    # Репозитории домена Users
│   │   │   ├── __init__.py
│   │   │   ├── user_repository.py    # CRUD пользователей
│   │   │   └── profile_repository.py # CRUD профилей
│   │   ├── trips/                    # Репозитории домена Trips
│   │   │   ├── __init__.py
│   │   │   ├── trip_repository.py    # CRUD поездок
│   │   │   ├── trip_point_repository.py # CRUD точек
│   │   │   ├── seat_repository.py    # CRUD мест
│   │   │   └── car_repository.py    # CRUD автомобилей
│   │   ├── requests/                 # Репозитории домена Requests
│   │   │   ├── __init__.py
│   │   │   └── request_repository.py # CRUD запросов
│   │   ├── chat/                     # Репозитории домена Chat
│   │   │   ├── __init__.py
│   │   │   ├── conversation_repository.py # CRUD бесед
│   │   │   └── message_repository.py # CRUD сообщений
│   │   ├── reviews/                  # Репозитории домена Reviews
│   │   │   ├── __init__.py
│   │   │   └── review_repository.py  # CRUD отзывов
│   │   ├── notifications/            # Репозитории домена Notifications
│   │   │   ├── __init__.py
│   │   │   └── notification_repository.py # CRUD уведомлений
│   │   └── admin/                    # Репозитории домена Admin
│   │       ├── __init__.py
│   │       ├── admin_repository.py   # CRUD администраторов
│   │       └── audit_repository.py   # Работа с аудитом
│   │
│   ├── utils/                        # Утилиты
│   │   ├── __init__.py
│   │   ├── helpers.py                # Общие хелперы
│   │   ├── email_utils.py           # Email утилиты
│   │   ├── date_utils.py            # Работа с датами
│   │   ├── validation_utils.py      # Валидация данных
│   │   └── pagination.py            # Пагинация
│   │
│   ├── locales/                      # Локализация
│   │   ├── __init__.py
│   │   ├── ru/                       # Русские переводы
│   │   │   └── messages.po
│   │   └── en/                       # Английские переводы
│   │       └── messages.po
│   │
│   └── main.py                       # Точка входа
│
├── tests/                            # Тесты
│   ├── __init__.py
│   ├── conftest.py                   # Fixtures для pytest
│   ├── test_auth/                    # Тесты Auth
│   ├── test_users/                   # Тесты Users
│   ├── test_trips/                   # Тесты Trips
│   ├── test_requests/                # Тесты Requests
│   ├── test_chat/                    # Тесты Chat
│   ├── test_reviews/                 # Тесты Reviews
│   ├── test_notifications/           # Тесты Notifications
│   └── test_admin/                   # Тесты Admin
│
├── alembic.ini                       # Конфигурация Alembic
├── docker-compose.yml                # Docker Compose
├── pyproject.toml                    # Зависимости
├── Dockerfile                        # Docker образ
├── .env.example                      # Пример переменных окружения
└── README.md                         # Документация
```

## Описание доменов

### Auth (Аутентификация)

**Ответственность:** Управление входом в систему, безопасностью и сессиями.

**Сущности:**
- Token — JWT токены доступа
- PasswordReset — токены сброса пароля

**Примечание:** Модель User находится в домене Users, так как пользователь — это сущность профиля, а не только аутентификации.

### Users (Пользователи)

**Ответственность:** Управление профилями пользователей, верификация, настройки.

**Сущности:**
- User — основная сущность пользователя
- UserProfile — расширенная информация профиля
- UserVerification — статус верификации (email, phone)
- UserPreferences — пользовательские настройки

**Почему выделен отдельно:** Профиль пользователя — это самостоятельная бизнес-сущность, которая используется во всех других доменах. Верификация и настройки имеют свою специфику.

### Trips (Поездки)

**Ответственность:** Создание, поиск и управление поездками.

**Сущности:**
- Trip — основная поездка (водитель, маршрут, дата, цена)
- TripPoint — точки маршрута (место отправления, промежуточные, прибытие)
- TripSeat — доступные места в поездке
- Car — информация об автомобиле водителя

**Почему выделен отдельно:** Это основной домен приложения, ради которого пользователи используют платформу. Имеет сложную логику поиска, фильтрации и управления местами.

### Requests (Запросы на бронирование)

**Ответственность:** Процесс бронирования мест в поездках.

**Сущности:**
- TripRequest — запрос на бронирование места
- RequestStatus — история изменения статусов

**Почему выделен отдельно:** Бронирование — это отдельный бизнес-процесс со своими статусами (pending, approved, rejected, cancelled). Требует согласования между водителем и пассажиром.

### Chat (Чат)

**Ответственность:** Коммуникация между пользователями в реальном времени.

**Сущности:**
- Conversation — беседа между двумя пользователями
- Message — отдельное сообщение
- MessageRead — статус прочтения

**Почему выделен отдельно:** Требует WebSocket коммуникации, имеет свою специфику хранения сообщений и онлайн-статуса. Может быть расширен для групповых чатов.

### Reviews (Отзывы)

**Ответственность:** Система отзывов и рейтингов после поездки.

**Сущности:**
- Review — текстовый отзыв
- ReviewRating — оценка (1-5 звезд)

**Почему выделен отдельно:** Отзывы создаются после завершения поездки и имеют специфический жизненный цикл (создание → возможная модерация → отображение).

### Notifications (Уведомления)

**Ответственность:** Отправка уведомлений через различные каналы.

**Сущности:**
- Notification — само уведомление
- NotificationChannel — канал (email, push, in-app)
- NotificationTemplate — шаблон уведомления

**Почему выделен отдельно:** Уведомления генерируются из многих доменов (новый запрос, новый отзыв, напоминание о поездке), поэтому вынесены в отдельный домен для переиспользуемости.

### Admin (Администрирование)

**Ответственность:** Модерация контента, управление администраторами, аудит.

**Сущности:**
- AdminUser — администратор системы
- AuditLog — журнал действий пользователей
- Moderation — модерация отзывов и поездок

**Почему выделен отдельно:** Административные функции имеют другие модели доступа и не должны смешиваться с пользовательским функционалом. Аудит важен для безопасности.

## Ключевые решения

### 1. Конфигурация

- Все настройки в `app/core/config.py`
- Переменные окружения через Pydantic Settings
- Отдельные профили: dev, test, prod

### 2. База данных

- Асинхронная SQLAlchemy 2.0
- Alembic для миграций
- Репозитории для доступа к данным

### 3. Авторизация

- JWT access токены
- Защита через зависимости FastAPI
- Расширяемость для 2FA

### 4. WebSocket

- Нативная поддержка в FastAPI
- HTTP fallback через polling
- Коммуникация в `app/api/websocket.py`

### 5. Локализация

- Структура для ru/en в `app/locales/`
- Pydantic схемы с поддержкой языка

### 6. Тестирование

- Pytest с async fixtures
- Тесты через FastAPI TestClient
- Покрытие core логики

## Готовность к расширению

Архитектура позволяет добавить:

- Payments — домен для платежей (stripe, apple pay)
- Favorites — избранные поездки и пользователи
- Reports — система жалоб на пользователей
- History — история поездок пользователя
- Search — полнотекстовый поиск (Elasticsearch)
- Analytics — аналитика для админов

## Зависимости между доменами

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer                            │
│  (Роутеры обращаются к сервисам, ничего не знают о БД) │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                  Services Layer                         │
│  (Сервисы обращаются к репозиториям и другим сервисам)  │
└─────────────────────────────────────────────────────────┘
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
    ┌───────────┐  ┌───────────────┐  ┌───────────┐
    │ Repos 1   │  │ Repos 2       │  │ Repos N   │
    │ (Trips)   │  │ (Users)       │  │ (Chat)    │
    └───────────┘  └───────────────┘  └───────────┘
            │              │              │
            └──────────────┼──────────────┘
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   Models Layer                          │
│         (SQLAlchemy модели — только структура)          │
└─────────────────────────────────────────────────────────┘
```

**Правило зависимостей:**
- API → Schemas → Services → Repositories → Models
- Домены могут зависеть от других доменов только через Services
- Репозитории одного домена не должны обращаться к моделям другого домена
