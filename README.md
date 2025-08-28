# Django + FastAPI + Celery + RabbitMQ + Postgres + Nginx

Готовый скелет проекта для разработки:

- **Django** — админка, модели, миграции.  
- **FastAPI** — эндпоинты с отдельной структурой (routes, schemas, settings).  
- **Celery + RabbitMQ** — фоновые и периодические задачи.  
- **Postgres** — база данных.  
- **Nginx** — reverse-proxy, раздаёт `/static/` и `/media/`, проксирует `/admin/` → Django, `/api/` → FastAPI.  
- **Docker Compose** — удобный запуск всех сервисов.  
- **.envs/** — переменные окружения по сервисам.  
- **tools/** — вспомогательные скрипты (`new_api_module.sh`, `rename_project.sh`).  

---

## Требования

- Docker (>= 24)  
- Docker Compose (v2)  
- GNU Make (опционально)  
- Bash (для скриптов)  

---

## Быстрый старт

1. Склонируйте репозиторий и перейдите в директорию:

   ```bash
   git clone <repo-url> myproject
   cd myproject
   ```

2. Настройте окружение в папке `.envs/` (по умолчанию уже есть базовые `.django`, `.postgres`, `.celery`, `.rabbitmq`, `.fastapi`).  
   Добавьте .envs/* в .gitignore

   Минимально — поменяйте `SECRET_KEY` и пароли для БД и RabbitMQ.

3. Поднимите проект:

   ```bash
   docker compose up --build
   ```

4. После запуска доступны:

   - Django Admin: [http://localhost/admin/](http://localhost/admin/)  
   - FastAPI Swagger: [http://localhost/api/docs](http://localhost/api/docs)  
   - RabbitMQ Management: [http://localhost:15672](http://localhost:15672)  
     (логин/пароль см. в `.envs/.rabbitmq`)

5. Создайте суперпользователя (однократно):

   ```bash
   docker compose exec django python src/manage.py createsuperuser
   ```

---

## Структура проекта

```
.
├─ compose/              # Dockerfile, entrypoints и конфиги
├─ src/
│  ├─ django_project/    # Django core
│  ├─ apps/              # Django apps
│  └─ fastapi_app/       # FastAPI со структурой
│     ├─ routes/         # Маршруты
│     ├─ schemas/        # Pydantic-схемы
│     ├─ settings/       # Config + logging
│     └─ core/           # зависимости, middlewares, exceptions
├─ tools/
│  ├─ new_api_module.sh  # создать новый модуль FastAPI (routes+schemas)
│  └─ rename_project.sh  # сменить имя проекта и API prefix
├─ docker-compose.yml    # главный compose файл
└─ .envs/                # переменные окружения
```

---

## Работа со скриптами

### Создание нового модуля FastAPI

Пример: хотим создать модуль `orders`.

```bash
chmod +x tools/new_api_module.sh
```

```bash
./tools/new_api_module.sh orders
```

Это создаст:
- `src/fastapi_app/routes/orders.py`
- `src/fastapi_app/schemas/orders.py`
- автоматически зарегистрирует роутер в `routes/__init__.py`

После рестарта контейнера FastAPI новый эндпоинт будет доступен.

### Переименование проекта

```bash
chmod +x tools/rename_project.sh
```

```bash
./tools/rename_project.sh "My Service"
```

Это обновит `.envs/.fastapi` и переименует проект логически (имя + API prefix).  
Чтобы изменения вступили в силу:

```bash
docker compose up -d --build
```

---

## Полезные команды

- Остановить и удалить контейнеры и данные:

  ```bash
  docker compose down -v
  ```

- Создать суперпользователя:

  ```bash
  docker compose exec django python src/manage.py createsuperuser
  ```

- Выполнить миграции:

  ```bash
  docker compose exec django python src/manage.py migrate
  ```

- Собрать статику (если нужно вручную):

  ```bash
  docker compose exec django python src/manage.py collectstatic --noinput
  ```

- Запустить Celery задачу вручную (в Django shell):

  ```bash
  docker compose exec django python src/manage.py shell -c "from apps.core.tasks import add; print(add.delay(2,3).get())"
  ```

---

## Дополнительно

- Для разработки удобно использовать `docker compose up -d` + логи по сервисам:

  ```bash
  docker compose logs -f django
  docker compose logs -f fastapi
  docker compose logs -f celery_worker
  ```

- Для продакшена можно добавить отдельный `docker-compose.override.yml` и Gunicorn/Uvicorn workers подстроить под сервер.

---
