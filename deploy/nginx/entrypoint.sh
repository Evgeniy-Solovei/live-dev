#!/bin/sh
set -eu

DOMAIN="${DOMAIN:-live-dev.by}"
CERTBOT_EMAIL="${CERTBOT_EMAIL:-live-dev@mail.ru}"
HTTP_TEMPLATE=/etc/nginx/templates-live/http.conf.template
HTTPS_TEMPLATE=/etc/nginx/templates-live/https.conf.template
ACTIVE_CONFIG=/etc/nginx/conf.d/default.conf
CERT_PATH="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"

render_config() {
  envsubst '${DOMAIN}' < "$1" > "$ACTIVE_CONFIG"
}

if [ -s "$CERT_PATH" ]; then
  render_config "$HTTPS_TEMPLATE"
else
  render_config "$HTTP_TEMPLATE"
fi

renew_certificates() {
  sleep 8
  while [ ! -s "$CERT_PATH" ]; do
    certbot certonly --webroot -w /var/www/certbot \
      --non-interactive --agree-tos --no-eff-email \
      --email "$CERTBOT_EMAIL" \
      -d "$DOMAIN" && {
        render_config "$HTTPS_TEMPLATE"
        nginx -s reload
        break
      }
    sleep 1800
  done

  while sleep 43200; do
    certbot renew --webroot -w /var/www/certbot \
      --quiet --deploy-hook "nginx -s reload" || true
  done
}

renew_certificates &
exec nginx -g 'daemon off;'
