import json
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, JsonResponse, HttpResponse, HttpResponseBadRequest
from django.urls import reverse
from django.utils.html import escape
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from core.models import SiteSettings
from core.utils import cached_json, client_ip, lookup_geo, inject_yandex_metrika
from django.conf import settings as django_settings


@require_GET
def home(request):
    """Serve the marketing site from FRONTEND_DIR (single Django app entry)."""
    index = Path(settings.FRONTEND_DIR) / 'index.html'
    if not index.is_file():
        raise Http404('Frontend index.html not found')
    html = inject_yandex_metrika(index.read_text(encoding='utf-8'))
    return HttpResponse(html, content_type='text/html; charset=utf-8')


@require_GET
def frontend_root_file(request, name: str):
    """Serve root frontend files like sw.js / build.json."""
    allowed = {'sw.js', 'build.json', 'robots.txt', 'sitemap.xml'}
    if name not in allowed:
        raise Http404()
    path = Path(settings.FRONTEND_DIR) / name
    if not path.is_file():
        raise Http404()
    content_types = {
        '.js': 'application/javascript',
        '.json': 'application/json',
        '.txt': 'text/plain; charset=utf-8',
        '.xml': 'application/xml; charset=utf-8',
    }
    content_type = content_types.get(path.suffix, 'application/octet-stream')
    return FileResponse(path.open('rb'), content_type=content_type)


@require_GET
def privacy(request):
    path = Path(settings.FRONTEND_DIR) / 'privacy.html'
    if not path.is_file():
        raise Http404('Privacy page not found')
    html = inject_yandex_metrika(path.read_text(encoding='utf-8'))
    return HttpResponse(html, content_type='text/html; charset=utf-8')


@require_GET
def sitemap(request):
    from content.seo import SERVICE_ORDER

    urls = [
        ('https://live-dev.by/', None, '1.0'),
        ('https://live-dev.by/privacy/', None, '0.2'),
    ]
    urls.extend(
        (f'https://live-dev.by{reverse("service_detail", args=[slug])}', None, '0.9')
        for slug in SERVICE_ORDER
    )
    entries = []
    for loc, lastmod, priority in urls:
        lastmod_xml = f'<lastmod>{lastmod}</lastmod>' if lastmod else ''
        entries.append(
            f'<url><loc>{escape(loc)}</loc>{lastmod_xml}'
            f'<changefreq>weekly</changefreq><priority>{priority}</priority></url>'
        )
    xml = '<?xml version="1.0" encoding="UTF-8"?>' \
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' \
          + ''.join(entries) + '</urlset>'
    return HttpResponse(xml, content_type='application/xml; charset=utf-8')


@cached_json('public_site_settings', getattr(django_settings, 'CACHE_TTL_SETTINGS', 120))
def _public_settings_payload():
    s = SiteSettings.load()
    return {
        'site_name': s.site_name,
        'contact_email': s.contact_email,
        'contact_phone': s.contact_phone,
        'contact_telegram': s.contact_telegram,
        'yandex_metrika_id': s.yandex_metrika_id,
        'yandex_metrika_webvisor': s.yandex_metrika_webvisor,
        'yandex_ads_enabled': s.yandex_ads_enabled,
        'yandex_ads_block_id': s.yandex_ads_block_id,
        'lead_goal_name': s.yandex_goal_name or 'lead_submit',
        'google_analytics_id': s.google_analytics_id,
        'google_ads_id': s.google_ads_id,
        'google_ads_conversion_label': s.google_ads_conversion_label,
        'google_tag_manager_id': s.google_tag_manager_id,
        'analytics_enabled': s.analytics_enabled,
    }


@require_GET
def public_settings(request):
    response = JsonResponse(_public_settings_payload())
    response['Cache-Control'] = 'public, max-age=60, stale-while-revalidate=300'
    return response


def _telegram_credentials():
    from core.models import SiteSettings

    s = SiteSettings.load()
    token = (s.telegram_bot_token or getattr(settings, 'TELEGRAM_BOT_TOKEN', '') or '').strip()
    chat_id = (s.telegram_chat_id or getattr(settings, 'TELEGRAM_CHAT_ID', '') or '').strip()
    return s, token, chat_id


def discover_telegram_chat(token: str | None = None) -> dict:
    """
    Берём последнего, кто написал боту (/start) — это и есть «куда слать».
    Telegram API иначе не умеет: бот не шлёт «в никуда», только в конкретный диалог.
    """
    import requests
    from core.models import SiteSettings

    s = SiteSettings.load()
    token = (token or s.telegram_bot_token or getattr(settings, 'TELEGRAM_BOT_TOKEN', '') or '').strip()
    if not token:
        return {'ok': False, 'error': 'Сначала вставь токен бота и сохрани настройки', 'chat_id': ''}

    try:
        resp = requests.get(
            f'https://api.telegram.org/bot{token}/getUpdates',
            params={'limit': 50, 'timeout': 0},
            timeout=10,
        )
        data = resp.json() if resp.content else {}
    except Exception as e:
        return {'ok': False, 'error': str(e), 'chat_id': ''}

    if not data.get('ok'):
        return {
            'ok': False,
            'error': data.get('description') or f'HTTP {resp.status_code}',
            'chat_id': '',
        }

    chat_id = ''
    chat_label = ''
    for upd in reversed(data.get('result') or []):
        msg = upd.get('message') or upd.get('edited_message') or upd.get('my_chat_member') or {}
        chat = msg.get('chat') if isinstance(msg, dict) else None
        if not chat and isinstance(msg, dict):
            chat = (msg.get('chat') or {})
        if not chat:
            # my_chat_member structure
            chat = (upd.get('my_chat_member') or {}).get('chat')
        if not chat:
            continue
        chat_id = str(chat.get('id') or '')
        if not chat_id:
            continue
        title = chat.get('title') or ' '.join(
            x for x in [chat.get('first_name'), chat.get('last_name')] if x
        ) or chat.get('username') or chat_id
        chat_label = title
        break

    if not chat_id:
        return {
            'ok': False,
            'error': 'Бот ещё ни от кого не получал сообщений. Открой своего бота в Telegram и нажми /start, потом снова «Подключить бота».',
            'chat_id': '',
        }

    s.telegram_chat_id = chat_id
    s.save(update_fields=['telegram_chat_id', 'updated_at'])
    return {'ok': True, 'error': None, 'chat_id': chat_id, 'label': chat_label}


def notify_telegram(text: str) -> dict:
    """
    Send message to Telegram. Returns {'ok': bool, 'error': str|None}.
    If chat_id empty — пробуем автоопределить по последнему /start.
    """
    import requests

    s, token, chat_id = _telegram_credentials()
    if not token:
        return {'ok': False, 'error': 'Не задан токен бота (Админка → Контакты и счётчики)'}

    if not chat_id:
        found = discover_telegram_chat(token)
        if not found.get('ok'):
            return {'ok': False, 'error': found.get('error') or 'Некуда слать: напиши боту /start'}
        chat_id = found['chat_id']

    try:
        resp = requests.post(
            f'https://api.telegram.org/bot{token}/sendMessage',
            json={
                'chat_id': chat_id,
                'text': text,
                'disable_web_page_preview': True,
            },
            timeout=8,
        )
        data = resp.json() if resp.content else {}
        if resp.ok and data.get('ok'):
            return {'ok': True, 'error': None}
        desc = (data.get('description') if isinstance(data, dict) else None) or f'HTTP {resp.status_code}'
        return {'ok': False, 'error': str(desc)}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
