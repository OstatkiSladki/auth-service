# WAL.md — Write-Ahead Log (состояние сессии)

Этот файл содержит текущее состояние проекта.

## Current Phase
**Auth Service Initialization — IN PROGRESS**

## Completed
- **Project Structure**: инициализирована структура проекта (`src/`, `tests/`), установлен пакетный менеджер `uv`, добавлены ключевые зависимости (FastAPI, SQLAlchemy, Alembic, pydantic-settings, asyncpg).
- **FastAPI Core**: реализован базовый `main.py` сервер с настроенными CORS middlewares согласно спецификации.
- **Database Settings**: реализовано подключение SQLAlchemy (асинхронное `asyncpg`), настроено хранение параметров в `src/core/config.py` и `.env`.
- **SQLAlchemy Models**: реализованы модели `User`, `RefreshToken`, `StaffProfile` с привязкой к схеме `"auth"`.
- **Enums Implementation (v1.2.1)**: добавлены `UsersRole` и `StaffRole` согласно пункту 3.3.1 спецификации. Модели обновлены для использования нативных PostgreSQL ENUM внутри схемы `auth`.
- **Alembic Init**: инициализирован и настроен Alembic для асинхронных миграций (`migrations/env.py` учитывает схему `auth`).

## In Progress
### DONE
- Завершена базовая инициализация каркаса и моделей с ролевой моделью.
- ✅ **Section 4 Implementation (API Endpoints):**
  - Реализованы все routes: Auth (register, login, refresh, logout, reset), Users (me, update, search), Staff Management
  - Добавлена поддержка HttpOnly Cookies с разными путями (/api/v1 для access, /api/v1/auth/refresh для refresh)
  - Все endpoints защищены JWT-токен проверкой через dependencies.py
  - ✅ **Staff Management Enhanced (v2):**
    - Реализована пагинация (используется `page`/`limit` через `StaffFilterParams`)
    - Добавлена фильтрация по роли сотрудника (role query parameter)
    - Добавлена сортировка (sort_by с поддержкой - префикса для обратного порядка)
    - Настроены методы репозитория на использование SQL JOIN (`joinedload` / `contains_eager`) вместо множественных N+1 запросов для подтягивания данных пользователя (`User`).
    - Все staff endpoints теперь возвращают полные данные пользователя + роль + метаданные пагинации
    - StaffMemberResponse содержит вложенный объект User с id, email, phone, name, role и т.д.
    - StaffListPaginatedResponse содержит массив StaffMemberResponse + total/page/limit/pages

### TODO
✅ Создание первой миграции Alembic (инициализировано и исправлено).
- Реальная отправка email писем для верификации и сброса пароля (сейчас заглушка).

### Future Implementation (Mocked for now)
- Подключение gRPC-клиента для вызова `CheckVenueExists` (заглушка в Staff management).
- Публикация событий в RabbitMQ `auth.staff.assigned` (оставлены TODO комментарии).
- Реальная отправка email писем для верификации и сброса пароля (заглушка моком).

## Known Issues
- Зависимость от локального PostgreSQL (требуется поднятие базы `db_auth` перед выполнением `uv run alembic revision --autogenerate`).

## Session Context
- **Start with**: поднятие БД, выполнение миграций и разработка эндпоинтов `/api/v1/auth/register`.
- **Key files**: 
  - `src/db/models/enums.py` (новые ролевые модели)
  - `src/db/models/*.py`
  - `main.py`
  - `src/core/config.py`
