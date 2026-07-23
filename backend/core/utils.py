from functools import wraps

from django.conf import settings
from django.core.cache import cache


def cached_json(key: str, ttl: int):
    """Cache callable JSON payload."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            hit = cache.get(key)
            if hit is not None:
                return hit
            data = fn(*args, **kwargs)
            cache.set(key, data, ttl)
            return data

        return wrapper

    return decorator


def client_ip(request) -> str | None:
    """Best-effort client IP behind nginx/proxy."""
    for header in ('HTTP_CF_CONNECTING_IP', 'HTTP_X_REAL_IP', 'HTTP_X_FORWARDED_FOR'):
        raw = request.META.get(header)
        if not raw:
            continue
        # X-Forwarded-For may be a list: client, proxy1, proxy2
        ip = raw.split(',')[0].strip()
        if ip:
            return ip
    return request.META.get('REMOTE_ADDR')


def yandex_metrika_head_html(counter_id: str | None = None, webvisor: bool | None = None) -> str:
    """
    Счётчик в HTML (не только через JS после /api/settings/).
    Нужен Яндекс.Директу: он ищет tag.js / номер счётчика в исходнике страницы.
    """
    if counter_id is None or webvisor is None:
        from core.models import SiteSettings

        s = SiteSettings.load()
        if counter_id is None:
            counter_id = s.yandex_metrika_id or ''
        if webvisor is None:
            webvisor = s.yandex_metrika_webvisor
    cid = str(counter_id or '').strip()
    if not cid.isdigit():
        return ''
    wv = 'true' if webvisor else 'false'
    # В исходнике страницы — иначе Директ пишет «на сайте нет счётчиков»
    return (
        f'<!-- Yandex.Metrika counter -->\n'
        f'<script type="text/javascript">\n'
        f'window.LIVEDEV_METRIKA_ID={cid!r};\n'
        f'window.__ldMetrikaInited=true;\n'
        f'(function(m,e,t,r,i){{\n'
        f'm[i]=m[i]||function(){{(m[i].a=m[i].a||[]).push(arguments)}};\n'
        f'm[i].l=1*new Date();\n'
        f'for(var j=0;j<document.scripts.length;j++){{if(document.scripts[j].src===r){{return}}}}\n'
        f'k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)\n'
        f'}})(window,document,"script","https://mc.yandex.ru/metrika/tag.js?id={cid}","ym");\n'
        f'ym({cid},"init",{{ssr:true,webvisor:{wv},clickmap:true,ecommerce:"dataLayer",'
        f'accurateTrackBounce:true,trackLinks:true}});\n'
        f'</script>\n'
        f'<noscript><div><img src="https://mc.yandex.ru/watch/{cid}" '
        f'style="position:absolute;left:-9999px" alt="" /></div></noscript>\n'
        f'<!-- /Yandex.Metrika counter -->\n'
    )


def inject_yandex_metrika(html: str) -> str:
    """Вставить счётчик перед </head>, если ещё нет."""
    if 'mc.yandex.ru/metrika' in html or 'Yandex.Metrika counter' in html:
        return html
    snippet = yandex_metrika_head_html()
    if not snippet:
        return html
    if '</head>' in html:
        return html.replace('</head>', snippet + '</head>', 1)
    return snippet + html


def _is_private_ip(ip: str) -> bool:
    try:
        from ipaddress import ip_address
        return ip_address(ip).is_private or ip_address(ip).is_loopback or ip_address(ip).is_link_local
    except ValueError:
        return True


def lookup_geo(ip: str | None) -> dict:
    """Free geo lookup (ip-api.com), cached. Empty on failure/private IP."""
    empty = {'country': '', 'country_code': '', 'city': ''}
    if not ip or _is_private_ip(ip):
        return empty

    cache_key = f'geo:{ip}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    result = dict(empty)
    ok = False
    try:
        import requests

        resp = requests.get(
            f'http://ip-api.com/json/{ip}',
            params={'fields': 'status,country,countryCode,city', 'lang': 'ru'},
            timeout=3,
        )
        if resp.ok:
            data = resp.json()
            if data.get('status') == 'success':
                result = {
                    'country': data.get('country') or '',
                    'country_code': data.get('countryCode') or '',
                    'city': data.get('city') or '',
                }
                ok = True
    except Exception:
        pass

    # Не кэшируем пустой ответ надолго — чтобы после сбоя API гео появилось
    ttl = getattr(settings, 'CACHE_TTL_GEO', 86400) if ok else 300
    cache.set(cache_key, result, ttl)
    return result


def detect_device(ua: str) -> str:
    ua_l = (ua or '').lower()
    if any(x in ua_l for x in ('mobile', 'android', 'iphone', 'ipod')):
        return 'mobile'
    if 'ipad' in ua_l or 'tablet' in ua_l:
        return 'tablet'
    return 'desktop'


def allow_request(scope: str, identity: str, limit: int, window: int = 60) -> bool:
    """Small fixed-window limiter; Nginx is the first line of defence in production."""
    key = f'ratelimit:{scope}:{identity or "unknown"}'
    if cache.add(key, 1, window):
        return True
    try:
        return cache.incr(key) <= limit
    except ValueError:
        cache.set(key, 1, window)
        return True
