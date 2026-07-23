# LiveDev Backend (Django)

Одно приложение: **сайт + API + админка**.

Только **PostgreSQL**.

## Локально (без Docker)

```bash
cd live-dev
source .venv/bin/activate
cd backend
python manage.py migrate
python manage.py seed_showcase --replace
python manage.py runserver
```

- Сайт: http://127.0.0.1:8000/
- Админка: http://127.0.0.1:8000/admin/

Фронт (HTML/CSS/JS/картинки): `../dev-agency-site-new/` → `FRONTEND_DIR`.

## Docker (один образ)

Из корня репозитория:

```bash
docker compose up --build
```

Сайт и админка: http://localhost/ до выпуска сертификата, затем https://live-dev.by/.

Файлы: корневой `Dockerfile` + `docker-compose.yml` (PostgreSQL, Django/Gunicorn и Nginx/Certbot).

## Production: live-dev.by

1. DNS A-запись `live-dev.by` должна указывать на IP сервера. Откройте входящие TCP-порты 80 и 443.
2. Скопируйте проект на сервер и заполните `backend/.env`. Обязательно задайте уникальный длинный `SECRET_KEY`, пароль PostgreSQL и пароль администратора.
3. Запустите:

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f nginx
```

Миграции и `collectstatic` выполняются при запуске `app`. Nginx сначала принимает HTTP-запрос для ACME-проверки, получает сертификат Let's Encrypt и автоматически переключается на HTTPS. Проверка продления выполняется каждые 12 часов.

PostgreSQL и Gunicorn не публикуют порты на сервере: они доступны только другим контейнерам. Наружу открыты только Nginx 80/443. `/assets/` и `/media/` раздаёт Nginx.

Проверка после запуска:

```bash
curl -I https://live-dev.by/
curl -I https://live-dev.by/assets/showcase/crm-1.webp
docker compose exec app python manage.py check --deploy
```

Если Docker-volume PostgreSQL уже был создан со старым паролем, изменение `.env` не меняет пароль существующей роли. Один раз выполните со старым рабочим окружением:

```bash
docker compose exec db psql -U livedev -d livedev -c "ALTER USER livedev WITH PASSWORD 'livedev2026solovey';"
docker compose restart app
```

## Перенос локальной базы и media

При обычном локальном запуске:

```bash
./deploy/export-local.sh
```

Команда создаст два файла в `backups/`: `database-*.dump` и `media-*.tar.gz`. Перенесите оба на сервер. После первого `docker compose up -d db` восстановите их:

```bash
./deploy/restore.sh backups/database-YYYYMMDD-HHMMSS.dump backups/media-YYYYMMDD-HHMMSS.tar.gz
```

`restore.sh` полностью заменяет содержимое целевой базы и Docker-volume media указанной резервной копией.

Для последующих резервных копий уже на Docker-сервере:

```bash
./deploy/backup.sh
```

Дамп PostgreSQL не содержит бинарные файлы из media, поэтому база и media всегда резервируются парой.

## Обслуживание аналитики

При необходимости удалить статистику старше года:

```bash
docker compose exec app python manage.py purge_old_analytics --days 365
```
