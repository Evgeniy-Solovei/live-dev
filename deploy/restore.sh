#!/bin/sh
set -eu

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 database.dump media.tar.gz" >&2
  exit 2
fi

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
DB_DUMP=$(CDPATH= cd -- "$(dirname -- "$1")" && pwd)/$(basename -- "$1")
MEDIA_ARCHIVE=$(CDPATH= cd -- "$(dirname -- "$2")" && pwd)/$(basename -- "$2")

cd "$ROOT_DIR"
docker compose up -d db
docker compose stop app nginx >/dev/null 2>&1 || true
docker compose exec -T db sh -c \
  'PGPASSWORD="$POSTGRES_PASSWORD" pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner' \
  < "$DB_DUMP"

docker run --rm \
  -v live-dev_media_data:/target \
  -v "$(dirname -- "$MEDIA_ARCHIVE"):/backup:ro" \
  alpine:3.20 sh -c \
  'find /target -mindepth 1 -delete && tar -xzf "/backup/$1" -C /target' \
  sh "$(basename -- "$MEDIA_ARCHIVE")"

docker compose up -d app nginx
echo "Database and media restored."
