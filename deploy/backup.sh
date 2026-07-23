#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
BACKUP_DIR="${1:-$ROOT_DIR/backups}"
STAMP=$(date +%Y%m%d-%H%M%S)
mkdir -p "$BACKUP_DIR"

cd "$ROOT_DIR"
docker compose exec -T db sh -c \
  'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' \
  > "$BACKUP_DIR/database-$STAMP.dump"

docker run --rm \
  -v live-dev_media_data:/source:ro \
  -v "$BACKUP_DIR:/backup" \
  alpine:3.20 \
  tar -czf "/backup/media-$STAMP.tar.gz" -C /source .

printf 'Database: %s\nMedia: %s\n' \
  "$BACKUP_DIR/database-$STAMP.dump" "$BACKUP_DIR/media-$STAMP.tar.gz"
