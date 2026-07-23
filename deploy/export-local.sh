#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
BACKUP_DIR="${1:-$ROOT_DIR/backups}"
STAMP=$(date +%Y%m%d-%H%M%S)
mkdir -p "$BACKUP_DIR"

set -a
. "$ROOT_DIR/backend/.env"
set +a

PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
  -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" \
  -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc \
  -f "$BACKUP_DIR/database-$STAMP.dump"

if [ -d "$ROOT_DIR/backend/media" ]; then
  tar -czf "$BACKUP_DIR/media-$STAMP.tar.gz" -C "$ROOT_DIR/backend/media" .
else
  tar -czf "$BACKUP_DIR/media-$STAMP.tar.gz" --files-from /dev/null
fi

printf 'Database: %s\nMedia: %s\n' \
  "$BACKUP_DIR/database-$STAMP.dump" "$BACKUP_DIR/media-$STAMP.tar.gz"
