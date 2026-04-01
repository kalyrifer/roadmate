# Доменная модель базы данных RoadMate

## Общая логика модели

Доменная модель построена на принципах **сущность-связь** (ER-модель) с учётом специфики сервиса совместных поездок. Центральной сущностью является `users` — все остальные таблицы так или иначе связаны с пользователями. Поездки (`trips`) являются основным бизнес-объектом, вокруг которого строятся заявки на бронирование (`trip_requests`), чаты (`conversations`, `messages`) и отзывы (`reviews`).

Модель использует подход **soft delete** для критически важных сущностей (пользователи, поездки) — физическое удаление не применяется, вместо этого используется поле `status` или `deleted_at`. Это обеспечивает целостность данных: отзывы не должны теряться при удалении пользователя, история поездок должна сохраняться для аналитики и аудита.

Все таблицы содержат служебные поля `created_at` и `updated_at` для отслеживания временных меток. Для сущностей с жизненным циклом (поездки, заявки, отзывы) добавляются специфичные временные метки: `confirmed_at`, `rejected_at`, `cancelled_at`, `read_at`.

Связи между таблицами спроектированы с учётом каскадных операций: при удалении пользователя его настройки удаляются (`ON DELETE CASCADE`), но поездки и отзывы остаются сnull-значениями во внешних ключах (`ON DELETE SET NULL`) — это сохраняет историю в системе.

---

## 1. Таблица users

### Назначение

Таблица `users` — центральная сущность системы, представляющая участников сервиса. Каждый пользователь может выступать как водитель (создаёт поездки) и как пассажир (подаёт заявки на бронирование). Таблица содержит аутентификационные данные, профильную информацию и рейтинговую систему.

### Поля

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `id` | UUID | Да | Уникальный идентификатор пользователя |
| `email` | VARCHAR(255) | Да | Email пользователя (уникальный) |
| `password_hash` | VARCHAR(255) | Да | Хэш пароля (bcrypt) |
| `first_name` | VARCHAR(100) | Да | Имя пользователя |
| `last_name` | VARCHAR(100) | Да | Фамилия пользователя |
| `phone` | VARCHAR(20) | Нет | Номер телефона |
| `avatar_url` | VARCHAR(500) | Нет | URL аватара |
| `bio` | TEXT | Нет | Описание профиля |
| `role` | ENUM | Да | Роль: `user`, `admin` |
| `rating` | DECIMAL(3,2) | Да | Средний рейтинг (0.00–5.00), default: 0.00 |
| `review_count` | INTEGER | Да | Количество отзывов, default: 0 |
| `is_active` | BOOLEAN | Да | Статус активности аккаунта, default: TRUE |
| `is_blocked` | BOOLEAN | Да | Флаг блокировки, default: FALSE |
| `email_verified` | BOOLEAN | Да | Подтверждение email, default: FALSE |
| `phone_verified` | BOOLEAN | Да | Подтверждение телефона, default: FALSE |
| `two_factor_enabled` | BOOLEAN | Да | 2FA включён, default: FALSE |
| `last_login_at` | TIMESTAMP | Нет | Время последнего входа |
| `created_at` | TIMESTAMP | Да | Время создания (default: now) |
| `updated_at` | TIMESTAMP | Да | Время последнего обновления |
| `deleted_at` | TIMESTAMP | Нет | Время мягкого удаления |

### Ограничения

- **UNIQUE**: `email` — email должен быть уникальным
- **UNIQUE**: `phone` — телефон должен быть уникальным (при наличии)
- **CHECK**: `rating` BETWEEN 0 AND 5 — рейтинг в пределах 0–5
- **CHECK**: `review_count` >= 0 — количество отзывов не может быть отрицательным

### Индексы

- `ix_users_email` — для быстрого поиска по email при аутентификации
- `ix_users_phone` — для поиска по телефону
- `ix_users_role` — для фильтрации по ролям (админы)
- `ix_users_is_active` — для фильтрации активных пользователей
- `ix_users_rating` — для сортировки по рейтингу

### Связи

- `user_settings` (1:1) — ONE-TO-ONE, `ON DELETE CASCADE`
- `trips` (1:N) — ONE-TO-MANY, `ON DELETE SET NULL` (поездки остаются при удалении водителя)
- `trip_requests` (1:N) — ONE-TO-MANY, `ON DELETE SET NULL`
- `conversations` (1:N) — ONE-TO-MANY, `ON DELETE SET NULL`
- `messages` (1:N) — ONE-TO-MANY, `ON DELETE SET NULL`
- `reviews_given` (1:N) — ONE-TO-MANY, `ON DELETE SET NULL`
- `reviews_received` (1:N) — ONE-TO-MANY, `ON DELETE SET NULL`
- `notifications` (1:N) — ONE-TO-MANY, `ON DELETE CASCADE`
- `audit_logs` (1:N) — ONE-TO-MANY, `ON DELETE CASCADE`

### Статусы и флаги

- `role`: `user` (обычный пользователь), `admin` (администратор)
- `is_active`: TRUE — аккаунт активен, FALSE — деактивирован пользователем
- `is_blocked`: TRUE — пользователь заблокирован администратором

### Future Extensions

- Поле `verification_token` для подтверждения email
- Поле `password_reset_token` и `password_reset_expires` для сброса пароля
- Поле `telegram_chat_id` для уведомлений в Telegram
- Поле `fcm_token` для push-уведомлений
- Поля для верификации водительских прав (`driver_license_number`, `driver_license_verified`)

---

## 2. Таблица trips

### Назначение

Таблица `trips` — основная бизнес-сущность сервиса, представляющая поездку, которую создаёт водитель. Поездка характеризуется маршрутом (откуда — куда), датой и временем, ценой за место, доступными местами и параметрами (багаж, курение, животные и т. д.).

### Поля

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `id` | UUID | Да | Уникальный идентификатор поездки |
| `driver_id` | UUID | Да | ID водителя (FK на users) |
| `from_city` | VARCHAR(100) | Да | Город отправления |
| `from_address` | VARCHAR(255) | Нет | Адрес отправления (точное место) |
| `to_city` | VARCHAR(100) | Да | Город назначения |
| `to_address` | VARCHAR(255) | Нет | Адрес назначения (точное место) |
| `departure_date` | DATE | Да | Дата поездки |
| `departure_time` | TIME | Да | Время отправления |
| `arrival_time` | TIME | Нет | Ориентировочное время прибытия |
| `price_per_seat` | DECIMAL(10,2) | Да | Цена за одно место |
| `total_seats` | INTEGER | Да | Всего мест в автомобиле |
| `available_seats` | INTEGER | Да | Доступные места |
| `description` | TEXT | Нет | Описание поездки |
| `luggage_allowed` | BOOLEAN | Да | Багаж разрешён, default: TRUE |
| `smoking_allowed` | BOOLEAN | Да | Курение разрешено, default: FALSE |
| `music_allowed` | BOOLEAN | Да | Музыка разрешена, default: TRUE |
| `pets_allowed` | BOOLEAN | Да | Животные разрешены, default: FALSE |
| `car_model` | VARCHAR(100) | Нет | Модель автомобиля |
| `car_color` | VARCHAR(50) | Нет | Цвет автомобиля |
| `car_license_plate` | VARCHAR(20) | Нет | Номерной знак |
| `status` | ENUM | Да | Статус поездки |
| `cancelled_at` | TIMESTAMP | Нет | Время отмены |
| `cancelled_reason` | TEXT | Нет | Причина отмены |
| `created_at` | TIMESTAMP | Да | Время создания |
| `updated_at` | TIMESTAMP | Да | Время последнего обновления |
| `deleted_at` | TIMESTAMP | Нет | Время мягкого удаления |

### Ограничения

- **FOREIGN KEY**: `driver_id` REFERENCES `users(id)` — связь с водителем
- **CHECK**: `total_seats` BETWEEN 1 AND 8 — мест может быть от 1 до 8
- **CHECK**: `available_seats` >= 0 AND <= `total_seats` — доступные места в пределах общего количества
- **CHECK**: `price_per_seat` > 0 — цена должна быть положительной

### Индексы

- `ix_trips_driver_id` — для поиска поездок конкретного водителя
- `ix_trips_from_city` — для поиска по городу отправления
- `ix_trips_to_city` — для поиска по городу назначения
- `ix_trips_departure_date` — для поиска по дате (основной индекс)
- `ix_trips_status` — для фильтрации по статусу
- `ix_trips_price_per_seat` — для фильтрации по цене
- `ix_trips_available_seats` — для фильтрации по доступности
- **COMPOSITE INDEX**: `ix_trips_route_search` (from_city, to_city, departure_date, status) — для главного поиска поездок

### Связи

- `users` (N:1) — водитель поездки, `ON DELETE SET NULL`
- `trip_requests` (1:N) — заявки на бронирование, `ON DELETE CASCADE`
- `conversations` (1:N) — связанные чаты, `ON DELETE CASCADE`
- `reviews` (1:N) — отзывы о поездке, `ON DELETE SET NULL`

### Статусы

- `draft` — черновик, поездка ещё не опубликована
- `published` — опубликована, доступна для бронирования
- `active` — активна (в процессе)
- `completed` — завершена
- `cancelled` — отменена водителем или администратором

### Timestamps

- `created_at` — создание поездки
- `updated_at` — любое изменение (редактирование, подтверждение заявок)
- `cancelled_at` — время отмены (если применимо)
- `deleted_at` — мягкое удаление

### Future Extensions

- Поле `intermediate_stops` (JSONB) — промежуточные точки маршрута
- Поле `route_coordinates` (JSONB) — координаты для карты
- Поле `estimated_distance` — расстояние в км
- Поле `estimated_duration` — примерное время в пути
- Поле `auto_cancel_after` — автоотмена, если никто не забронировал

---

## 3. Таблица trip_requests

### Назначение

Таблица `trip_requests` представляет заявку пассажира на бронирование места в конкретной поездке. Заявка проходит жизненный цикл: отправлена → подтверждена/отклонена → отменена. Система контролирует дубликаты и проверяет доступность мест перед подтверждением.

### Поля

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `id` | UUID | Да | Уникальный идентификатор заявки |
| `trip_id` | UUID | Да | ID поездки (FK на trips) |
| `passenger_id` | UUID | Да | ID пассажира (FK на users) |
| `seats_requested` | INTEGER | Да | Количество запрашиваемых мест |
| `message` | TEXT | Нет | Сообщение водителю от пассажира |
| `status` | ENUM | Да | Статус заявки |
| `confirmed_at` | TIMESTAMP | Нет | Время подтверждения |
| `rejected_at` | TIMESTAMP | Нет | Время отклонения |
| `rejected_reason` | TEXT | Нет | Причина отклонения |
| `cancelled_at` | TIMESTAMP | Нет | Время отмены |
| `cancelled_by` | ENUM | Нет | Кем отменена: `passenger`, `driver`, `admin` |
| `created_at` | TIMESTAMP | Да | Время создания заявки |
| `updated_at` | TIMESTAMP | Да | Время последнего обновления |
| `deleted_at` | TIMESTAMP | Нет | Время мягкого удаления |

### Ограничения

- **FOREIGN KEY**: `trip_id` REFERENCES `trips(id)` — связь с поездкой, `ON DELETE CASCADE`
- **FOREIGN KEY**: `passenger_id` REFERENCES `users(id)` — связь с пассажиром, `ON DELETE CASCADE`
- **UNIQUE**: `uq_trip_passenger` — пара (trip_id, passenger_id) уникальна, один пассажир — одна активная заявка на поездку
- **CHECK**: `seats_requested` BETWEEN 1 AND 8 — мест может быть от 1 до 8

### Индексы

- `ix_trip_requests_trip_id` — поиск заявок по поездке
- `ix_trip_requests_passenger_id` — поиск заявок по пассажиру
- `ix_trip_requests_status` — фильтрация по статусу
- `ix_trip_requests_created_at` — сортировка по времени

### Связи

- `trips` (N:1) — поездка, `ON DELETE CASCADE`
- `users` (N:1) — пассажир, `ON DELETE CASCADE`
- `conversations` (1:N) — связанный чат, `ON DELETE CASCADE`

### Статусы

- `pending` — ожидает решения водителя
- `confirmed` — подтверждена водителем
- `rejected` — отклонена водителем
- `cancelled` — отменена пассажиром, водителем или администратором

### Timestamps

- `created_at` — подача заявки
- `updated_at` — любое изменение статуса
- `confirmed_at` — время подтверждения (заполняется при переходе в статус confirmed)
- `rejected_at` — время отклонения (заполняется при переходе в статус rejected)
- `cancelled_at` — время отмены (заполняется при переходе в статус cancelled)

### Бизнес-логика

- **Контроль дубликатов**: UNIQUE constraint на пару (trip_id, passenger_id) предотвращает создание повторных заявок
- **Проверка мест**: перед подтверждением заявки система должна проверить, что `available_seats >= seats_requested`
- **Автоотклонение**: при отмене поездки все pending-заявки автоматически переводятся в статус cancelled

### Future Extensions

- Поле `passenger_rating` — оценка пассажира водителем (после поездки)
- Поле `driver_rating` — оценка водителя пассажиром
- Поле `is_premium` — премиум-заявка с приоритетом

---

## 4. Таблица conversations

### Назначение

Таблица `conversations` представляет диалог между пользователями. Диалог всегда привязан к контексту — поездке или заявке на бронирование. Это позволяет сохранять историю общения в рамках конкретной поездки и избегать создания дубликатов чатов.

### Поля

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `id` | UUID | Да | Уникальный идентификатор диалога |
| `trip_id` | UUID | Нет | ID поездки (FK на trips) |
| `trip_request_id` | UUID | Нет | ID заявки (FK на trip_requests) |
| `initiator_id` | UUID | Да | ID пользователя, инициировавшего диалог |
| `participant_id` | UUID | Да | ID второго участника |
| `last_message_at` | TIMESTAMP | Нет | Время последнего сообщения |
| `status` | ENUM | Да | Статус диалога |
| `created_at` | TIMESTAMP | Да | Время создания |
| `updated_at` | TIMESTAMP | Да | Время последнего обновления |
| `deleted_at` | TIMESTAMP | Нет | Время мягкого удаления |

### Ограничения

- **FOREIGN KEY**: `trip_id` REFERENCES `trips(id)` — связь с поездкой, `ON DELETE SET NULL`
- **FOREIGN KEY**: `trip_request_id` REFERENCES `trip_requests(id)` — связь с заявкой, `ON DELETE SET NULL`
- **FOREIGN KEY**: `initiator_id` REFERENCES `users(id)` — инициатор, `ON DELETE SET NULL`
- **FOREIGN KEY**: `participant_id` REFERENCES `users(id)` — участник, `ON DELETE SET NULL`
- **CHECK**: хотя бы один из `trip_id` или `trip_request_id` должен быть NOT NULL — диалог должен иметь контекст

### Индексы

- `ix_conversations_trip_id` — поиск чатов по поездке
- `ix_conversations_trip_request_id` — поиск чатов по заявке
- `ix_conversations_initiator_id` — поиск чатов инициатора
- `ix_conversations_participant_id` — поиск чатов участника
- `ix_conversations_last_message_at` — сортировка по времени последнего сообщения

### Связи

- `trips` (N:1) — поездка (опционально), `ON DELETE SET NULL`
- `trip_requests` (N:1) — заявка (опционально), `ON DELETE SET NULL`
- `users_initiator` (N:1) — инициатор, `ON DELETE SET NULL`
- `users_participant` (N:1) — участник, `ON DELETE SET NULL`
- `messages` (1:N) — сообщения в диалоге, `ON DELETE CASCADE`

### Статусы

- `active` — диалог активен
- `archived` — архивирован пользователем
- `blocked` — заблокирован (при жалобе)

### Логика связывания

Диалог создаётся в контексте заявки (`trip_request_id`) — это предпочтительный сценарий. Если заявки нет (например, водитель и пассажир общаются до подачи заявки), диалог привязывается к поездке (`trip_id`).

### Future Extensions

- Поле `subject` — тема диалога
- Поле `is_pinned` — закреплённый диалог
- Поле `mute_until` — время игнорирования уведомлений

---

## 5. Таблица messages

### Назначение

Таблица `messages` хранит отдельные сообщения внутри диалогов. Каждое сообщение принадлежит конкретному диалогу и отправителю, имеет индикатор прочтения и временную метку.

### Поля

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `id` | UUID | Да | Уникальный идентификатор сообщения |
| `conversation_id` | UUID | Да | ID диалога (FK на conversations) |
| `sender_id` | UUID | Да | ID отправителя (FK на users) |
| `content` | TEXT | Да | Текст сообщения |
| `message_type` | ENUM | Да | Тип сообщения |
| `is_read` | BOOLEAN | Да | Прочитано, default: FALSE |
| `read_at` | TIMESTAMP | Нет | Время прочтения |
| `created_at` | TIMESTAMP | Да | Время отправки |
| `updated_at` | TIMESTAMP | Да | Время редактирования |
| `deleted_at` | TIMESTAMP | Нет | Время удаления (мягкое) |

### Ограничения

- **FOREIGN KEY**: `conversation_id` REFERENCES `conversations(id)` — связь с диалогом, `ON DELETE CASCADE`
- **FOREIGN KEY**: `sender_id` REFERENCES `users(id)` — связь с отправителем, `ON DELETE SET NULL`

### Индексы

- `ix_messages_conversation_id` — поиск сообщений в диалоге
- `ix_messages_sender_id` — поиск сообщений по отправителю
- `ix_messages_created_at` — сортировка по времени
- `ix_messages_is_read` — фильтрация непрочитанных
- **COMPOSITE INDEX**: `ix_messages_conversation_unread` (conversation_id, is_read, created_at) — для получения непрочитанных

### Связи

- `conversations` (N:1) — диалог, `ON DELETE CASCADE`
- `users` (N:1) — отправитель, `ON DELETE SET NULL`

### Типы сообщений

- `text` — обычное текстовое сообщение
- `system` — системное сообщение (автоматическое)
- `image` — изображение (future)
- `location` — геолокация (future)

### Timestamps

- `created_at` — отправка сообщения (не изменяется при редактировании)
- `updated_at` — время последнего редактирования
- `read_at` — время прочтения (заполняется при переходе is_read в TRUE)

### Future Extensions

- Поле `attachments` (JSONB) — вложения
- Поле `delivery_status` — статус доставки (sent, delivered, failed)
- Поле `reply_to_id` — ответ на конкретное сообщение

---

## 6. Таблица reviews

### Назначение

Таблица `reviews` хранит отзывы, которые участники поездки оставляют друг другу после её завершения. Отзывы формируют рейтинг пользователя и являются ключевым элементом доверия в сервисе.

### Поля

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `id` | UUID | Да | Уникальный идентификатор отзыва |
| `trip_id` | UUID | Да | ID поездки (FK на trips) |
| `author_id` | UUID | Да | ID автора отзыва (FK на users) |
| `target_id` | UUID | Да | ID пользователя, которому оставлен отзыв |
| `rating` | INTEGER | Да | Оценка (1–5) |
| `comment` | TEXT | Нет | Текст отзыва |
| `category` | ENUM | Нет | Категория отзыва |
| `status` | ENUM | Да | Статус публикации |
| `moderated_at` | TIMESTAMP | Нет | Время модерации |
| `moderated_by` | UUID | Нет | ID модератора (FK на users) |
| `created_at` | TIMESTAMP | Да | Время создания |
| `updated_at` | TIMESTAMP | Да | Время обновления |
| `deleted_at` | TIMESTAMP | Нет | Время удаления |

### Ограничения

- **FOREIGN KEY**: `trip_id` REFERENCES `trips(id)` — связь с поездкой, `ON DELETE CASCADE`
- **FOREIGN KEY**: `author_id` REFERENCES `users(id)` — автор, `ON DELETE CASCADE`
- **FOREIGN KEY**: `target_id` REFERENCES `users(id)` — получатель, `ON DELETE CASCADE`
- **FOREIGN KEY**: `moderated_by` REFERENCES `users(id)` — модератор, `ON DELETE SET NULL`
- **UNIQUE**: `uq_review_author_trip` — уникальность: один автор — один отзыв на поездку
- **CHECK**: `rating` BETWEEN 1 AND 5 — оценка от 1 до 5

### Индексы

- `ix_reviews_trip_id` — поиск отзывов по поездке
- `ix_reviews_author_id` — поиск отзывов автора
- `ix_reviews_target_id` — поиск отзывов о пользователе
- `ix_reviews_rating` — фильтрация по рейтингу
- `ix_reviews_status` — фильтрация по статусу модерации
- **COMPOSITE INDEX**: `ix_reviews_target_rating` (target_id, rating) — для расчёта среднего рейтинга

### Связи

- `trips` (N:1) — поездка, `ON DELETE CASCADE`
- `users_author` (N:1) — автор отзыва, `ON DELETE CASCADE`
- `users_target` (N:1) — получатель отзыва, `ON DELETE CASCADE`
- `users_moderator` (N:1) — модератор (опционально), `ON DELETE SET NULL`

### Статусы

- `pending` — ожидает модерации
- `published` — опубликован
- `hidden` — скрыт модератором
- `rejected` — отклонён

### Категории

- `driver_punctuality` — пунктуальность водителя
- `driver_behavior` — поведение водителя
- `comfort` — комфорт поездки
- `passenger_behavior` — поведение пассажира
- `general` — общий отзыв

### Бизнес-логика

- **Уникальность**: автор может оставить только один отзыв на поездку (UNIQUE constraint)
- **Участники поездки**: отзыв может оставить только участник поездки (проверка на уровне приложения)
- **Агрегация рейтинга**: при создании/удалении отзыва пересчитывается `rating` и `review_count` в таблице users

### Timestamps

- `created_at` — создание отзыва
- `updated_at` — редактирование
- `moderated_at` — время модерации

### Future Extensions

- Поле `response` — ответ на отзыв
- Поле `photos` (JSONB) — фотографии
- Поле `reaction` — реакции (лайк/дизлайк)

---

## 7. Таблица notifications

### Назначение

Таблица `notifications` хранит уведомления для пользователей. Уведомления генерируются системой при значимых событиях: новая заявка, подтверждение поездки, новое сообщение, отзыв и т. д.

### Поля

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `id` | UUID | Да | Уникальный идентификатор |
| `user_id` | UUID | Да | ID получателя (FK на users) |
| `type` | ENUM | Да | Тип уведомления |
| `title` | VARCHAR(200) | Да | Заголовок уведомления |
| `message` | TEXT | Да | Текст уведомления |
| `data` | JSONB | Нет | Дополнительные данные (payload) |
| `is_read` | BOOLEAN | Да | Прочитано, default: FALSE |
| `read_at` | TIMESTAMP | Нет | Время прочтения |
| `trip_id` | UUID | Нет | Связанная поездка |
| `trip_request_id` | UUID | Нет | Связанная заявка |
| `conversation_id` | UUID | Нет | Связанный чат |
| `created_at` | TIMESTAMP | Да | Время создания |
| `updated_at` | TIMESTAMP | Да | Время обновления |
| `deleted_at` | TIMESTAMP | Нет | Время удаления |

### Ограничения

- **FOREIGN KEY**: `user_id` REFERENCES `users(id)` — получатель, `ON DELETE CASCADE`
- **FOREIGN KEY**: `trip_id` REFERENCES `trips(id)` — поездка (опционально), `ON DELETE SET NULL`
- **FOREIGN KEY**: `trip_request_id` REFERENCES `trip_requests(id)` — заявка (опционально), `ON DELETE SET NULL`
- **FOREIGN KEY**: `conversation_id` REFERENCES `conversations(id)` — чат (опционально), `ON DELETE SET NULL`

### Индексы

- `ix_notifications_user_id` — поиск уведомлений пользователя
- `ix_notifications_type` — фильтрация по типу
- `ix_notifications_is_read` — фильтрация непрочитанных
- `ix_notifications_created_at` — сортировка по времени
- **COMPOSITE INDEX**: `ix_notifications_user_unread` (user_id, is_read, created_at) — для получения непрочитанных

### Связи

- `users` (N:1) — получатель, `ON DELETE CASCADE`
- `trips` (N:1) — связанная поездка, `ON DELETE SET NULL`
- `trip_requests` (N:1) — связанная заявка, `ON DELETE SET NULL`
- `conversations` (N:1) — связанный чат, `ON DELETE SET NULL`

### Типы уведомлений

- `trip_request_new` — новая заявка на поездку
- `trip_request_confirmed` — заявка подтверждена
- `trip_request_rejected` — заявка отклонена
- `trip_request_cancelled` — заявка отменена
- `trip_created` — поездка создана
- `trip_cancelled` — поездка отменена
- `trip_completed` — поездка завершена
- `message_new` — новое сообщение
- `review_received` — получен отзыв
- `system` — системное уведомление

### Future Extensions

- Поля `email_sent`, `push_sent`, `telegram_sent` — статусы доставки в каналах
- Поле `scheduled_at` — запланированная отправка
- Поле `expired_at` — время истечения (для временных уведомлений)

---

## 8. Таблица audit_logs

### Назначение

Таблица `audit_logs` предназначена для записи всех значимых действий в системе. Она служит для отладки, расследования инцидентов, анализа поведения пользователей и обеспечения безопасности.

### Поля

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `id` | UUID | Да | Уникальный идентификатор |
| `user_id` | UUID | Нет | ID пользователя, совершившего действие |
| `action` | VARCHAR(50) | Да | Тип действия |
| `entity_type` | VARCHAR(50) | Да | Тип сущности |
| `entity_id` | UUID | Нет | ID сущности |
| `old_values` | JSONB | Нет | Предыдущие значения (для обновлений) |
| `new_values` | JSONB | Нет | Новые значения (для созданий/обновлений) |
| `metadata` | JSONB | Нет | Дополнительные данные (IP, User-Agent и т. д.) |
| `status` | ENUM | Да | Результат операции |
| `error_message` | TEXT | Нет | Сообщение об ошибке |
| `ip_address` | INET | Нет | IP-адрес |
| `user_agent` | VARCHAR(500) | Нет | User-Agent браузера/клиента |
| `created_at` | TIMESTAMP | Да | Время события |

### Ограничения

- **FOREIGN KEY**: `user_id` REFERENCES `users(id)` — пользователь (опционально, действия могут быть системными), `ON DELETE SET NULL`

### Индексы

- `ix_audit_logs_user_id` — поиск действий пользователя
- `ix_audit_logs_action` — фильтрация по типу действия
- `ix_audit_logs_entity_type` — фильтрация по типу сущности
- `ix_audit_logs_entity_id` — поиск по ID сущности
- **COMPOSITE INDEX**: `ix_audit_logs_entity` (entity_type, entity_id) — поиск всех действий с сущностью
- `ix_audit_logs_created_at` — временной анализ
- **COMPOSITE INDEX**: `ix_audit_logs_user_action` (user_id, action, created_at) — история действий пользователя

### Связи

- `users` (N:1) — пользователь, совершивший действие, `ON DELETE SET NULL`

### Типы действий

- `user_login` — вход в систему
- `user_logout` — выход
- `user_register` — регистрация
- `user_password_change` — смена пароля
- `trip_create` — создание поездки
- `trip_update` — обновление поездки
- `trip_cancel` — отмена поездки
- `trip_request_create` — создание заявки
- `trip_request_confirm` — подтверждение заявки
- `trip_request_reject` — отклонение заявки
- `message_send` — отправка сообщения
- `review_create` — создание отзыва

### Статусы

- `success` — действие выполнено успешно
- `failed` — действие не удалось

### Future Extensions

- Поле `request_id` — ID HTTP-запроса для трассировки
- Поле `session_id` — ID сессии
- Таблицы для архивирования старых логов

---

## 9. Таблица user_settings

### Назначение

Таблица `user_settings` хранит индивидуальные настройки пользователя. Связь ONE-TO-ONE с таблицей users позволяет иметь единый экземпляр настроек для каждого пользователя.

### Поля

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `id` | UUID | Да | Уникальный идентификатор |
| `user_id` | UUID | Да | ID пользователя (FK на users) |
| `language` | VARCHAR(10) | Да | Язык интерфейса, default: 'ru' |
| `notifications_enabled` | BOOLEAN | Да | Включены ли уведомления, default: TRUE |
| `email_notifications` | BOOLEAN | Да | Уведомления на email, default: TRUE |
| `push_notifications` | BOOLEAN | Да | Push-уведомления, default: TRUE |
| `telegram_notifications` | BOOLEAN | Да | Уведомления в Telegram, default: FALSE |
| `trip_request_notifications` | BOOLEAN | Да | Уведомления о заявках, default: TRUE |
| `message_notifications` | BOOLEAN | Да | Уведомления о сообщениях, default: TRUE |
| `review_notifications` | BOOLEAN | Да | Уведомления об отзывах, default: TRUE |
| `marketing_notifications` | BOOLEAN | Да | Маркетинговые уведомления, default: FALSE |
| `privacy_show_profile` | BOOLEAN | Да | Показывать профиль, default: TRUE |
| `privacy_show_phone` | BOOLEAN | Да | Показывать телефон, default: TRUE |
| `privacy_show_last_seen` | BOOLEAN | Да | Показывать последний визит, default: TRUE |
| `timezone` | VARCHAR(50) | Да | Часовой пояс, default: 'Europe/Moscow' |
| `is_active` | BOOLEAN | Да | Настройки активны, default: TRUE |
| `created_at` | TIMESTAMP | Да | Время создания |
| `updated_at` | TIMESTAMP | Да | Время обновления |
| `deleted_at` | TIMESTAMP | Нет | Время удаления |

### Ограниждения

- **FOREIGN KEY**: `user_id` REFERENCES `users(id)` — связь с пользователем, `ON DELETE CASCADE`
- **UNIQUE**: `uq_user_settings_user_id` — только одни настройки на пользователя

### Индексы

- `ix_user_settings_user_id` — поиск настроек по пользователю (уникальный)
- `ix_user_settings_language` — фильтрация по языку

### Связи

- `users` (1:1) — пользователь, `ON DELETE CASCADE`

### Future Extensions

- Поле `theme` — тема оформления (light/dark)
- Поле `currency` — предпочитаемая валюта
- Поле `distance_unit` — единицы расстояния (km/miles)
- JSONB-поля для расширенных настроек уведомлений
- Поле `favorite_routes` — избранные маршруты

---

## Сводная таблица связей между сущностями

| Родительская таблица | Дочерняя таблица | Тип связи | FK на родителя | ON DELETE |
|---------------------|------------------|-----------|----------------|-----------|
| users | user_settings | 1:1 | user_id | CASCADE |
| users | trips | 1:N | driver_id | SET NULL |
| users | trip_requests | 1:N | passenger_id | CASCADE |
| users | conversations | 1:N | initiator_id, participant_id | SET NULL |
| users | messages | 1:N | sender_id | SET NULL |
| users | reviews (author) | 1:N | author_id | CASCADE |
| users | reviews (target) | 1:N | target_id | CASCADE |
| users | notifications | 1:N | user_id | CASCADE |
| users | audit_logs | 1:N | user_id | SET NULL |
| trips | trip_requests | 1:N | trip_id | CASCADE |
| trips | conversations | 1:N | trip_id | SET NULL |
| trips | reviews | 1:N | trip_id | CASCADE |
| trip_requests | conversations | 1:N | trip_request_id | SET NULL |
| conversations | messages | 1:N | conversation_id | CASCADE |

---

## Уникальные ограничения (UNIQUE)

| Таблица | Поле/комбинация | Назначение |
|---------|-----------------|-------------|
| users | email | Один аккаунт на email |
| users | phone | Один аккаунт на телефон |
| user_settings | user_id | Одни настройки на пользователя |
| trip_requests | trip_id + passenger_id | Одна активная заявка на поездку |
| reviews | trip_id + author_id | Один отзыв от автора на поездку |

---

## Индексируемые поля

### Первичные индексы (автоматические)

- `id` — во всех таблицах (PRIMARY KEY)

### Дополнительные индексы

| Таблица | Поле | Индекс | Назначение |
|---------|------|--------|-------------|
| users | email | ix_users_email | Аутентификация |
| users | phone | ix_users_phone | Поиск по телефону |
| users | role | ix_users_role | Фильтрация админов |
| users | is_active | ix_users_is_active | Фильтрация активных |
| trips | driver_id | ix_trips_driver_id | Поиск поездок водителя |
| trips | from_city | ix_trips_from_city | Поиск по городу отправления |
| trips | to_city | ix_trips_to_city | Поиск по городу назначения |
| trips | departure_date | ix_trips_departure_date | Поиск по дате |
| trips | status | ix_trips_status | Фильтрация по статусу |
| trips | price_per_seat | ix_trips_price_per_seat | Фильтрация по цене |
| trips | from_city, to_city, departure_date, status | ix_trips_route_search | Главный поиск |
| trip_requests | trip_id | ix_trip_requests_trip_id | Заявки поездки |
| trip_requests | passenger_id | ix_trip_requests_passenger_id | Заявки пользователя |
| trip_requests | status | ix_trip_requests_status | Фильтрация по статусу |
| conversations | trip_id | ix_conversations_trip_id | Чат поездки |
| conversations | participant_id | ix_conversations_participant_id | Чат пользователя |
| messages | conversation_id | ix_messages_conversation_id | Сообщения чата |
| messages | is_read | ix_messages_is_read | Непрочитанные |
| reviews | trip_id | ix_reviews_trip_id | Отзывы поездки |
| reviews | target_id | ix_reviews_target_id | Отзывы о пользователе |
| notifications | user_id | ix_notifications_user_id | Уведомления пользователя |
| notifications | is_read | ix_notifications_is_read | Непрочитанные |
| audit_logs | user_id | ix_audit_logs_user_id | Логи пользователя |
| audit_logs | entity_type, entity_id | ix_audit_logs_entity | Логи сущности |

---

## Потенциальные места для расширения

### 1. Географические данные

- Таблица `cities` — справочник городов с координатами
- Таблица `addresses` — сохранённые адреса пользователей

### 2. Платежи

- Таблица `payments` — история платежей
- Таблица `promocodes` — промокоды

### 3. Водительские функции

- Таблица `driver_documents` — документы водителя
- Таблица `vehicle_inspections` — техосмотры

### 4. Чат

- Таблица `message_attachments` — вложения
- Таблица `conversation_participants` — участники (для групповых чатов)

### 5. Уведомления

- Таблица `notification_channels` — каналы доставки
- Таблица `notification_templates` — шаблоны

### 6. Аналитика

- Таблица `trip_views` — статистика просмотров поездок
- Таблица `search_queries` — поисковые запросы

---

## Заключение

Представленная модель данных спроектирована с учётом следующих принципов:

1. **Нормализация** — данные не дублируются, связи обеспечивают целостность
2. **Масштабируемость** — индексы построены под основные сценарии использования (поиск поездок, фильтрация заявок, уведомления)
3. **Аудируемость** — все значимые действия записываются в audit_logs
4. **Безопасность** — soft delete сохраняет историю, пароли хранятся в хэшированном виде
5. **Расширяемость** — JSONB-поля и enum-типы позволяют добавлять новую функциональность без миграций структуры
6. **Производительность** — композитные индексы оптимизируют главные поисковые сценарии

Модель готова для реализации в SQLAlchemy с использованием Alembic для миграций.
