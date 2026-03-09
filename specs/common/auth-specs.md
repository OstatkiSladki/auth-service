# Спецификация сервиса: Auth Service (v1.2)

## 1. Общие сведения

| Параметр             | Значение                                                                           |
| :------------------- | :--------------------------------------------------------------------------------- |
| **Название сервиса** | `auth-service`                                                                     |
| **Версия**           | 1.2.0                                                                              |
| **Назначение**       | Централизованное управление идентификацией, авторизацией и профилями пользователей |

---

## 2. Цели и Задачи

### 2.1. Основные цели
1. **Безопасная аутентификация** — обеспечение входа/регистрации пользователей с защитой от XSS и CSRF атак
2. **Управление сессиями** — выдача, обновление и отзыв токенов доступа
3. **Восстановление доступа** — безопасный сброс пароля и подтверждение Email
4. **Управление персоналом** — привязка пользователей к площадкам (Venues) с ролевой моделью
5. **Интеграция** — предоставление данных о пользователе другим сервисам системы

### 2.2. Функциональные требования
- Регистрация и вход пользователей по Email/Password
- Выдача пары Access + Refresh токенов (JWT)
- Автоматическое обновление Access токена через Refresh
- Подтверждение Email и сброс пароля через JWT-токены (stateless)
- Создание и управление профилями сотрудников (staff profiles)
- Поиск пользователей по Email (для менеджеров)
- Публикация событий в RabbitMQ для уведомлений

---

## 3. Архитектурные решения

### 3.1. Стек технологий

| Компонент | Технология | Версия |
| :--- | :--- | :--- |
| **Язык** | Python | 3.11+ |
| **Framework** | FastAPI | 0.100+ |
| **ORM** | SQLAlchemy (Async) | 2.0+ |
| **Миграции** | Alembic | Latest |
| **БД** | PostgreSQL | 15+ |
| **Message Broker** | RabbitMQ | 3.11+ |
| **RPC** | gRPC (grpcio) | Latest |
| **Password Hashing** | Argon2-cffi | Latest |
| **Tokens** | JWT (PyJWT) | Latest |
| **Контейнеризация** | Docker | Latest |

### 3.2. Хранение токенов (Критическое решение)

| Токен | Где храним | Как передаем | Время жизни | Путь Cookie |
| :--- | :--- | :--- | :--- | :--- |
| **Access Token** | HttpOnly Cookie | Автоматически (Browser) | 30 минут | `/api/v1` |
| **Refresh Token** | HttpOnly Cookie | Автоматически (Browser) | 30 дней | `/api/v1/auth/refresh` |

**Преимущества:**
- ✅ Защита от XSS (JavaScript не имеет доступа к HttpOnly Cookie)
- ✅ Защита от CSRF (SameSite=Lax + Secure)
- ✅ Удобство для фронтенда (не нужно управлять токенами вручную)
- ✅ Изоляция (разные пути ограничивают область действия токенов)

### 3.3. Схема базы данных

```sql
-- =============================================
-- AUTH SERVICE - db_auth
-- Таблицы: users, refresh_tokens, staff_profiles
-- =============================================

-- USERS
CREATE TABLE "public"."users" (
    "id" BIGSERIAL PRIMARY KEY,
    "email" VARCHAR(255) NOT NULL UNIQUE,
    "phone" VARCHAR(20) UNIQUE,
    "password_hash" VARCHAR(255) NOT NULL,
    "first_name" VARCHAR(100) NOT NULL,
    "last_name" VARCHAR(100),
    "avatar_url" TEXT,
    "is_active" BOOLEAN DEFAULT TRUE,
    "is_verified" BOOLEAN DEFAULT FALSE,
    "privacy_policy_accepted_at" TIMESTAMP WITH TIME ZONE,
    "default_address" TEXT,
    "preferences_json" JSONB DEFAULT '{}',
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "deleted_at" TIMESTAMP WITH TIME ZONE
);

-- REFRESH TOKENS
CREATE TABLE "public"."refresh_tokens" (
    "id" BIGSERIAL PRIMARY KEY,
    "user_id" BIGINT NOT NULL,
    "token_hash" VARCHAR(255) NOT NULL UNIQUE,
    "ip_address" INET,
    "user_agent" TEXT,
    "expires_at" TIMESTAMP WITH TIME ZONE NOT NULL,
    "is_revoked" BOOLEAN DEFAULT FALSE,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "last_used_at" TIMESTAMP WITH TIME ZONE,
    CONSTRAINT "fk_refresh_tokens_user" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE CASCADE
);
CREATE INDEX "refresh_tokens_idx_user" ON "public"."refresh_tokens" ("user_id", "is_revoked");
CREATE INDEX "refresh_tokens_idx_expires" ON "public"."refresh_tokens" ("expires_at");

-- STAFF PROFILES
CREATE TABLE "public"."staff_profiles" (
    "id" BIGSERIAL PRIMARY KEY,
    "user_id" BIGINT NOT NULL UNIQUE,
    "venue_id" BIGINT NOT NULL,
    "role" VARCHAR(50) DEFAULT 'staff',
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "fk_staff_user" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE CASCADE
);
CREATE INDEX "staff_profiles_idx_venue" ON "public"."staff_profiles" ("venue_id");
CREATE INDEX "staff_profiles_idx_user" ON "public"."staff_profiles" ("user_id");
```

**Примечания:**
- `venue_id` в `staff_profiles` не имеет FK — валидация через gRPC вызов в Venue Service
- `deleted_at` в `users` поддерживает soft-delete (GDPR compliance)
- `preferences_json` хранит пользовательские настройки в формате JSONB

### 3.3.1 - добавление в схему бд

В таблице staff_profiles мы должны использовать следующий enum (и на уровне базы и на уровне приложения для ролей) (базово staff всегда роль для новых сотрудников)
```
class StaffRole(str, Enum):
    """
    Роли сотрудника в рамках конкретной площадки (Venue).
    """
    STAFF = "staff"       # Базовый исполнитель
    MANAGER = "manager"   # Операционное управление
    ADMIN = "admin"       # Полные права на площадку
    OWNER = "owner"       # Владелец площадки (высшая роль)
```
---

А также в таблице users должны быть роли 
```
class UsersRole(str, Enum):
   USER = "user"
   STAFF = "staff"
   ADMIN = "admin"
```
По умолчанию всегда ставим user, если назначают сотруднком на точку - меняем на staff, роль админа добавляется только из бд и нужна на внутреннем уровне для управления всем сервисом - это быстрая индикация ролей 



## 4. API Маршруты и Функционал

### 4.1. Authentication (Публичные эндпоинты)

| Метод | Endpoint | Описание | Auth | Cookies |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Регистрация нового пользователя + установка токенов | No | Set Access + Refresh |
| `POST` | `/api/v1/auth/login` | Вход по email/password + установка токенов | No | Set Access + Refresh |
| `POST` | `/api/v1/auth/refresh` | Обновление Access токена (Refresh из Cookie) | No | Set new Access |
| `POST` | `/api/v1/auth/logout` | Выход + отзыв Refresh токена в БД + очистка Cookies | Yes | Clear all Cookies |
| `POST` | `/api/v1/auth/password/reset-request` | Генерация JWT-токена сброса + отправка Email | No | - |
| `POST` | `/api/v1/auth/password/reset` | Установка нового пароля по токену из письма | No | - |
| `POST` | `/api/v1/auth/email/verify` | Подтверждение Email по токену из письма | No | - |

**Логика работы:**

1. **Register/Login:**
   - Проверка уникальности email/phone
   - Хеширование пароля (Argon2)
   - Генерация Access + Refresh токенов
   - Сохранение хеша Refresh токена в БД
   - Установка Cookies (HttpOnly, Secure, SameSite=Lax)
   - Возврат профиля пользователя в теле ответа

2. **Refresh:**
   - Извлечение Refresh токена из Cookie (путь `/api/v1/auth/refresh`)
   - Проверка в БД: существует, не отозван, не истек
   - Проверка `user.is_active`
   - Генерация нового Access токена
   - Обновление `last_used_at` у Refresh токена
   - Установка нового Access Cookie

3. **Logout:**
   - Извлечение Refresh токена из Cookie
   - Установка `is_revoked=True` в БД
   - Очистка всех Cookies (Max-Age=0)

4. **Password Reset:**
   - Генерация JWT-токена с `purpose: reset_password`, TTL 15 мин
   - Публикация события в RabbitMQ (`auth.password.reset.requested`)
   - Notification Service отправляет Email
   - Пользователь переходит по ссылке → токен в URL → POST на `/reset`
   - Проверка токена → смена пароля → отзыв всех Refresh токенов пользователя

5. **Email Verify:**
   - Аналогично сбросу пароля (JWT-токен с `purpose: verify_email`)
   - Установка `is_verified=True` у пользователя

---

### 4.2. User Profile (Требует аутентификации)

| Метод | Endpoint | Описание | Auth |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/users/me` | Получить профиль текущего пользователя | Yes (Cookie) |
| `PATCH` | `/api/v1/users/me` | Обновить профиль текущего пользователя | Yes (Cookie) |
| `GET` | `/api/v1/users/search` | Поиск пользователя по Email (для менеджеров) | Yes (Cookie) |

**Логика работы:**

1. **GET /me:**
   - Извлечение Access токена из Cookie (путь `/api/v1`)
   - Валидация JWT (подпись, exp, iat)
   - Загрузка пользователя из БД по `user_id` из токена
   - Возврат полного профиля + staff_profile (если есть)

2. **PATCH /me:**
   - Валидация токена
   - Обновление только переданных полей
   - Авто-обновление `updated_at` (триггер БД)

3. **GET /search:**
   - Валидация токена
   - Поиск пользователя по email (параметр query)
   - Возврат только публичных данных (id, name, avatar, email)
   - Используется менеджерами для добавления сотрудников

---

#### 4.3. Staff Management (Требует аутентификации + права)

| Метод    | Endpoint                          | Описание                       | Auth | Права                           |
| :------- | :-------------------------------- | :----------------------------- | :--- | :------------------------------ |
| `POST`   | `/api/v1/venues/{venue_id}/staff` | Добавить сотрудника (Другого)  | Yes  | Manager/Admin venue             |
| `GET`    | `/api/v1/venues/{venue_id}/staff` | Список сотрудников площадки с пагинацией и фильтрацией | Yes  | Manager/Admin venue             |
| `GET`    | `/api/v1/staff/{profile_id}`      | Профиль конкретного сотрудника с полными данными пользователя | Yes  | Manager/Admin или сам сотрудник |
| `PATCH`  | `/api/v1/staff/{profile_id}`      | Редактирование сотрудника      | Yes  | Manager/Admin venue             |
| `DELETE` | `/api/v1/staff/{profile_id}`      | Удаление сотрудника (отвязка)  | Yes  | Manager/Admin venue             |

**Логика работы:**

1. **POST /venues/{venue_id}/staff (Добавление сотрудника):**
   - Проверка: текущий пользователь — менеджер/админ этого venue
   - Поиск пользователя по `user_email` из тела запроса
   - Проверка: нет ли уже профиля у этого пользователя
   - gRPC вызов в Venue Service: `CheckVenueExists(venue_id)`
   - Создание записи в `staff_profiles` с указанной ролью
   - Обновление роли пользователя на `staff` (если была `user`)
   - Публикация события `auth.staff.assigned` в RabbitMQ
   - Возврат полного профиля сотрудника с данными пользователя

2. **GET /venues/{venue_id}/staff (Список сотрудников):**
   - Проверка прав доступа к venue (менеджер/админ)
   - Поддержка параметров пагинации и фильтрации (в выделенной схеме `StaffFilterParams`):
     - `page: int` (по умолчанию 1) — страница
     - `limit: int` (по умолчанию 20, макс 100) — количество записей на странице
     - `role: str` (опционально) — фильтр по роли сотрудника (staff, manager, admin, owner)
     - `sort_by: str` (опционально, по умолчанию `-created_at`) — сортировка по полям (created_at, first_name, last_name, role, email)
   - Возврат объекта с массивом сотрудников, каждый содержит полную информацию пользователя + роль + метаданные пагинации (total, page, limit, pages)

3. **GET /staff/{profile_id} (Профиль конкретного сотрудника):**
   - Проверка прав доступа (сам сотрудник или менеджер/админ его venue)
   - Возврат полного профиля сотрудника с полной информацией пользователя (id, email, имя, фамилия, телефон, роль пользователя, роль сотрудника, и т.д.)

4. **PATCH /staff/{profile_id} (Редактирование сотрудника):**
   - Проверка прав (менеджер/админ venue)
   - Обновление `role` сотрудника
   - Возврат обновленного профиля с полной информацией пользователя

5. **DELETE /staff/{profile_id} (Удаление/отвязка сотрудника):**
   - Проверка прав (менеджер/админ venue)
   - Удаление связи пользователя с площадкой (не удаляет пользователя из системы)
   - Возвращает статус 204 No Content

---

## 5. Внутренние интерфейсы (gRPC)

### 5.1. AuthService (Сервер)

| Метод | Описание | Потребитель |
| :--- | :--- | :--- |
| `ValidateToken` | Валидация токена (интроспекция) | Другие сервисы |
| `GetUserById` | Получение данных пользователя по ID | Другие сервисы |
| `CheckUserExists` | Проверка существования пользователя | Другие сервисы |
| `RevokeStaffAccess` | Отзыв доступа стаффа при удалении площадки | Venue Service |

### 5.2. VenueService (Клиент из Auth)

| Метод | Описание | Когда вызывается |
| :--- | :--- | :--- |
| `CheckVenueExists` | Проверка существования площадки | При создании staff профиля |

**Примечание:** Синхронный gRPC вызов. При недоступности Venue Service — ошибка 400.

---

## 6. События RabbitMQ

**Exchange:** `auth.events` (Topic)

| Routing Key           | Payload                                            | Потребитель          | Описание                                  |
| :-------------------- | :------------------------------------------------- | :------------------- | :---------------------------------------- |
| `auth.staff.assigned` | `{ "user_id": 1, "venue_id": 5, "role": "staff" }` | Notification Service | Уведомление о назначении сотрудником      |
| `auth.user.deleted`   | `{ "user_id": 1 }`                                 | Все сервисы          | Soft-delete пользователя (очистка данных) |

**Механизм публикации:**
- Асинхронная публикация через `BackgroundTasks` (для MVP)
- В будущем — Outbox Pattern для гарантированной доставки

---

## 7. Безопасность

### 7.1. Пароли
- **Алгоритм:** Argon2id
- **Параметры:** time_cost=3, memory_cost=65536, parallelism=4
- **Минимальная длина:** 8 символов
- **Хранение:** Только хеш в БД (`password_hash`)

### 7.2. Токены
- **Алгоритм:** JWT (HS256 для MVP, RS256 для продакшена)
- **Access Token:** 30 минут,Claims: `sub`, `email`, `roles`, `exp`, `iat`
- **Refresh Token:** 30 дней, хранится в БД (хеш), отзываемый
- **Секрет:** Переменная окружения `JWT_SECRET_KEY` (мин. 32 байта)

### 7.3. Cookies
| Атрибут | Значение | Описание |
| :--- | :--- | :--- |
| `HttpOnly` | True | Защита от XSS (JS не имеет доступа) |
| `Secure` | True | Только HTTPS (в продакшене) |
| `SameSite` | Lax | Защита от CSRF |
| `Path` | Разный | Изоляция токенов по путям |
| `Domain` | `.company.com` | Для работы на поддоменах |

### 7.4. CORS
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.company.com"],  # Конкретный домен
    allow_credentials=True,  # ОБЯЗАТЕЛЬНО для Cookies
    allow_methods=["POST", "GET", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

### 7.5. Rate Limiting
- Реализуется на уровне **Nginx** (limit_req)
- `/login`, `/reset-request`: 5 запросов в минуту с IP
- `/refresh`: 30 запросов в минуту
- Остальные эндпоинты: стандартные лимиты

---

## 8. Структура проекта

```
auth-service/
├── .venv/                          # Виртуальное окружение (uv)
├── .gitignore
├── .python-version                 # Версия Python для uv
├── pyproject.toml                  # Зависимости и метаданные (uv)
├── uv.lock                         # Lock file (uv)
├── alembic.ini                     # Конфигурация Alembic
├── Dockerfile
├── .dockerignore
├── main.py                         # Точка входа приложения
│
├── migrations/                     # Alembic миграции
│   ├── versions/
│   └── env.py
│
├── src/                            # Исходный код приложения
│   ├── __init__.py
│   │
│   ├── api/                        # API слой (роутеры)
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── router.py           # Агрегатор всех роутеров v1
│   │   │   │
│   │   │   ├── auth/               # Аутентификация
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py       # Эндпоинты /auth/*
│   │   │   │   ├── schemas.py      # Pydantic схемы для auth
│   │   │   │   └── service.py      # Бизнес-логика auth
│   │   │   │
│   │   │   ├── users/              # Пользователи
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py       # Эндпоинты /users/*
│   │   │   │   ├── schemas.py      # Pydantic схемы для users
│   │   │   │   └── service.py      # Бизнес-логика users
│   │   │   │
│   │   │   └── staff/              # Сотрудники
│   │   │       ├── __init__.py
│   │   │       ├── router.py       # Эндпоинты /staff/*
│   │   │       ├── schemas.py      # Pydantic схемы для staff
│   │   │       └── service.py      # Бизнес-логика staff
│   │   │
│   │   └── deps.py                 # Зависимости FastAPI (get_current_user, etc.)
│   │
│   ├── db/                         # Слой работы с данными
│   │   ├── __init__.py
│   │   ├── base.py                 # Базовый класс для моделей
│   │   ├── session.py              # Создание сессий БД
│   │   │
│   │   ├── models/                 # SQLAlchemy модели
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── token.py
│   │   │   └── staff.py
│   │   │
│   │   └── repositories/           # Репозитории (паттерн Repository)
│   │       ├── __init__.py
│   │       ├── base.py             # Базовый репозиторий (CRUD)
│   │       ├── user.py
│   │       ├── token.py
│   │       └── staff.py
│   │
│   ├── core/                       # Ядро приложения
│   │   ├── __init__.py
│   │   ├── config.py               # Настройки из env
│   │   ├── security.py             # Argon2, JWT, хеширование
│   │   └── events.py               # RabbitMQ publisher
│   │
│   ├── services/                   # Внешние сервисы (gRPC клиенты)
│   │   ├── __init__.py
│   │   ├── venue_client.py         # gRPC клиент для Venue Service
│   │   └── notification_client.py  # gRPC клиент для Notification Service
│   │
│   └── rpc/                        # gRPC сервер (для других сервисов)
│       ├── __init__.py
│       ├── proto/                  # .proto файлы
│       │   └── auth.proto
│       └── services.py             # Реализация gRPC сервисов
│
└── tests/                          # Тесты
    ├── __init__.py
    ├── conftest.py
    ├── unit/
    └── integration/
```
