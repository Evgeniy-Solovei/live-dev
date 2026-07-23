#!/bin/sh
set -e

echo "Waiting for Postgres..."
python - <<'PY'
import os, time
import psycopg
host=os.environ.get("POSTGRES_HOST","db")
port=os.environ.get("POSTGRES_PORT","5432")
user=os.environ.get("POSTGRES_USER","livedev")
password=os.environ.get("POSTGRES_PASSWORD","livedev")
dbname=os.environ.get("POSTGRES_DB","livedev")
for i in range(60):
    try:
        with psycopg.connect(host=host, port=port, user=user, password=password, dbname=dbname) as conn:
            print("Postgres is up")
            break
    except Exception as e:
        print("retry", i, e)
        time.sleep(1)
else:
    raise SystemExit("Postgres not ready")
PY

python manage.py migrate --noinput

# Пустая витрина → fixtures/initial_content.json (первый деплой).
# Есть данные в pgdata → не трогаем.
# Принудительно: SEED_SHOWCASE_REPLACE=1
FIXTURE="fixtures/initial_content.json"
if [ "${SEED_SHOWCASE_REPLACE:-0}" = "1" ]; then
  if [ -f "$FIXTURE" ]; then
    echo "Force load fixture (SEED_SHOWCASE_REPLACE=1)"
    python manage.py load_initial_content --replace --path "$FIXTURE"
  else
    echo "No fixture — seed_showcase --replace"
    python manage.py seed_showcase --replace
  fi
elif [ -f "$FIXTURE" ]; then
  python manage.py load_initial_content --path "$FIXTURE"
else
  python - <<'PY'
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from content.models import ShowcaseItem
from django.core.management import call_command
if ShowcaseItem.objects.exists():
    print('Showcase already has data — skip')
else:
    print('No fixture — seed_showcase')
    call_command('seed_showcase', replace=True)
PY
fi

python manage.py collectstatic --noinput

if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ]; then
  python manage.py shell <<'PY'
import os
from django.contrib.auth import get_user_model
User=get_user_model()
u=os.environ['DJANGO_SUPERUSER_USERNAME']
e=os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
p=os.environ['DJANGO_SUPERUSER_PASSWORD']
if not User.objects.filter(username=u).exists():
    User.objects.create_superuser(u, e, p)
    print('superuser created')
else:
    print('superuser exists')
PY
fi

exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-3}" \
  --timeout 60 \
  --graceful-timeout 30 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --access-logfile - \
  --error-logfile -
