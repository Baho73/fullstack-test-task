# Fullstack Test Task — File Exchange MVP

## Выполненные задачи

### 1. Рефакторинг бэкенда

Монолитный `service.py` разбит на layered architecture:

```
backend/src/
├── database.py                  # Единый async engine, session factory, FastAPI DI
├── models.py                    # ORM модели с cascade delete (StoredFile → Alert)
├── schemas.py                   # Pydantic V2 схемы + PaginatedResponse[T]
├── storage.py                   # Файловые операции со streaming upload (64KB chunks)
├── app.py                       # FastAPI routes с Depends(get_session) и pagination
├── tasks.py                     # Celery tasks на shared DB module (без дублирования engine)
├── repositories/
│   ├── file_repository.py       # Data access: CRUD + пагинация для StoredFile
│   └── alert_repository.py      # Data access: CRUD + пагинация для Alert
└── services/
    ├── file_service.py          # Бизнес-логика файлов: upload, cascade delete, download
    └── alert_service.py         # Бизнес-логика алертов
```

**Ключевые архитектурные решения:**
- **Dependency Injection** — сессии БД инжектируются через `Depends(get_session)`, не создаются внутри функций
- **Repository pattern** — data access отделён от бизнес-логики
- **Единый DB module** — `database.py` как single source of truth (устранено дублирование engine в tasks.py)

### 2. Исправленные баги и оптимизации

| Баг | Исправление |
|-----|------------|
| PostgreSQL порт: `PGPORT=5433`, но контейнер слушает 5432 | Исправлен на `PGPORT=5432`, порт-маппинг `5432:5432` |
| Удаление файла вызывает FK violation (алерты не удаляются) | Cascade delete через ORM relationship + `ON DELETE CASCADE` на FK |
| Дублирование `engine`/`session_maker` в `tasks.py` | Единый `database.py` модуль, tasks используют `async_session_maker` из него |
| Файл загружается целиком в память (`content = await upload_file.read()`) | Streaming upload через 64KB chunks в `storage.py` |
| Frontend Dockerfile копирует несуществующий `.env.production` | Строка удалена из Dockerfile |
| `alembic env.py` импортирует удалённый `src.service` | Обновлён на `src.database.DATABASE_URL` |
| Backend не зависит от Redis в docker-compose | Добавлен `depends_on: backend-redis` |
| `FileUpdate` принимает пустой title | Добавлена валидация через `@field_validator` |

### 3. Рефакторинг фронтенда

Монолитный `page.tsx` (~370 строк) разбит на слои:

```
frontend/src/
├── types/index.ts               # FileItem, AlertItem, PaginatedResponse<T>
├── api/client.ts                # fetchFiles, fetchAlerts, uploadFile (configurable base URL)
├── components/
│   ├── Pagination.tsx           # Переиспользуемый компонент пагинации
│   ├── FilesTable.tsx           # Таблица файлов
│   ├── AlertsTable.tsx          # Таблица алертов
│   └── UploadModal.tsx          # Модальное окно загрузки
└── app/page.tsx                 # Тонкий оркестратор (~130 строк)
```

- API URL вынесен в `NEXT_PUBLIC_API_URL` (не захардкожен `localhost:8000`)
- Типы переиспользуются через `@/types` алиас

### 4. Пагинация (бэк + фронт)

**Бэкенд:** `GET /files` и `GET /alerts` принимают `limit` (1-100, default 20) и `offset` (>=0) query params. Возвращают:

```json
{
  "items": [...],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

**Фронтенд:** компонент `PaginationControl` с номерами страниц, prev/next, first/last. Независимая пагинация для файлов и алертов.

### 5. Тесты

67 тестов: unit + integration.

```
backend/tests/
├── conftest.py                  # Async SQLite engine, session fixtures, factory helpers
├── unit/
│   ├── test_database.py         # Session factory, get_session DI
│   ├── test_models.py           # Schema, FK, cascade delete
│   ├── test_schemas.py          # Validation, PaginatedResponse
│   ├── test_storage.py          # Save/delete/get_path
│   ├── test_file_repository.py  # Paginated CRUD
│   ├── test_alert_repository.py # Paginated CRUD, cascade
│   ├── test_file_service.py     # Business logic, cascade delete, 404, empty file
│   ├── test_alert_service.py    # Pagination, alert creation
│   └── test_tasks.py            # Scan (.exe, size, mime), metadata, alerts
└── integration/
    └── test_api.py              # HTTP endpoints via httpx.AsyncClient
```

**Стек тестирования:** pytest + pytest-asyncio, httpx, aiosqlite (in-memory SQLite для unit-тестов, без Docker).

```bash
# Запуск тестов
cd backend
uv sync --group dev
uv run pytest tests/ -v
```

## Запуск

```bash
docker compose -f docker-compose.dev.yml up
docker exec -it backend alembic upgrade head
```

**Фронт:** http://localhost:3000/test

**Бэк (Swagger):** http://localhost:8000/docs
