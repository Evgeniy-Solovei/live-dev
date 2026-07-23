# Единый образ LiveDev: сайт + API + админка
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FRONTEND_DIR=/app/frontend

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
RUN chmod +x /app/entrypoint.sh

COPY dev-agency-site-new/index.html /app/frontend/index.html
COPY dev-agency-site-new/sw.js /app/frontend/sw.js
COPY dev-agency-site-new/build.json /app/frontend/build.json
COPY dev-agency-site-new/robots.txt /app/frontend/robots.txt
COPY dev-agency-site-new/sitemap.xml /app/frontend/sitemap.xml
COPY dev-agency-site-new/privacy.html /app/frontend/privacy.html
COPY dev-agency-site-new/assets /app/frontend/assets

EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
