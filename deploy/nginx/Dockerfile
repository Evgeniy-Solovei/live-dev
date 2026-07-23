FROM nginx:1.27-alpine

COPY dev-agency-site-new/assets /srv/frontend/assets
COPY deploy/nginx/templates /etc/nginx/templates-live
COPY deploy/nginx/templates/http.conf.template /etc/nginx/templates/default.conf.template
