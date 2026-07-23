FROM nginx:1.27-alpine

RUN apk add --no-cache certbot

COPY dev-agency-site-new/assets /srv/frontend/assets
COPY deploy/nginx/templates /etc/nginx/templates-live
COPY deploy/nginx/entrypoint.sh /entrypoint-live.sh
RUN chmod +x /entrypoint-live.sh

ENTRYPOINT ["/entrypoint-live.sh"]
