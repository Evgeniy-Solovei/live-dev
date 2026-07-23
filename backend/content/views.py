import json
import json as json_module
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404, HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods

from content.models import ShowcaseCategory, ShowcaseItem
from content.seo import SERVICES, SERVICE_ORDER
from core.models import SiteSettings
from core.utils import cached_json


@cached_json('public_showcase', getattr(settings, 'CACHE_TTL_SHOWCASE', 300))
def _showcase_payload():
    data = {}
    categories = (
        ShowcaseCategory.objects.filter(is_active=True)
        .prefetch_related('items')
        .order_by('sort_order', 'id')
    )
    for cat in categories:
        items = []
        for item in cat.items.filter(is_active=True).order_by('sort_order', 'id'):
            image = item.resolved_image
            v = int(item.updated_at.timestamp()) if item.updated_at else 0
            if image and v and '?' not in image:
                image = f'{image}?v={v}'
            items.append({
                'id': item.id,
                'title': item.title,
                'text': item.text,
                'points': item.points or [],
                'image': image,
                'updated_at': item.updated_at.isoformat() if item.updated_at else '',
            })
        if items:
            data[cat.slug] = {
                'label': cat.label,
                'items': items,
            }
    return data


@require_GET
def public_showcase(request):
    response = JsonResponse(_showcase_payload())
    response['Cache-Control'] = 'public, max-age=60, stale-while-revalidate=300'
    return response


CATEGORY_SERVICE = {
    'crm': 'crm-sistemy',
    'telegram': 'telegram-mini-app',
    'bots': 'telegram-boty',
    'landings': 'landing-page',
    'shop': 'razrabotka-saitov',
    'ai': 'ai-avtomatizaciya',
    'vpn': 'podderzhka-proektov',
}


def _safe_schema(data):
    return json_module.dumps(data, ensure_ascii=False).replace('<', '\\u003c')


def _seo_common():
    return {
        'services_nav': [(slug, SERVICES[slug]['h1']) for slug in SERVICE_ORDER],
        'site_settings': SiteSettings.load(),
    }


@require_GET
def service_detail(request, slug):
    service = SERVICES.get(slug)
    if not service:
        raise Http404('Service not found')

    index = Path(settings.FRONTEND_DIR) / 'index.html'
    if not index.is_file():
        raise Http404('Frontend index.html not found')
    canonical = f'https://live-dev.by{reverse("service_detail", args=[slug])}'
    category = service['category_slugs'][0]
    schema = {
        '@context': 'https://schema.org',
        '@type': 'Service',
        'name': service['h1'],
        'description': service['description'],
        'url': canonical,
        'areaServed': [
            {'@type': 'City', 'name': 'Витебск'},
            {'@type': 'Country', 'name': 'Беларусь'},
        ],
        'provider': {
            '@type': 'ProfessionalService',
            'name': 'LiveDev',
            'url': 'https://live-dev.by/',
            'email': 'live-dev@mail.ru',
            'telephone': '+375298945462',
        },
    }
    html = index.read_text(encoding='utf-8')
    replacements = {
        '<title>Разработка сайтов, CRM и Telegram в Витебске — LiveDev</title>': f'<title>{service["title"]}</title>',
        '<meta name="description" content="Разрабатываем сайты, CRM, Telegram Mini Apps, ботов и AI-решения под ключ в Витебске и удалённо по Беларуси. Аналитика, интеграции и запуск." />': f'<meta name="description" content="{service["description"]}" />',
        '<meta property="og:title" content="Разработка сайтов и программного обеспечения — LiveDev" />': f'<meta property="og:title" content="{service["title"]}" />',
        '<meta property="og:description" content="Сайты, CRM, Telegram Mini Apps, боты и AI-автоматизация для бизнеса. Бесплатный разбор задачи за 20–30 минут." />': f'<meta property="og:description" content="{service["description"]}" />',
        '<meta property="og:url" content="https://live-dev.by/" />': f'<meta property="og:url" content="{canonical}" />',
        '<link rel="canonical" href="https://live-dev.by/" />': f'<link rel="canonical" href="{canonical}" />',
    }
    for source, target in replacements.items():
        html = html.replace(source, target, 1)
    page_data = (
        f'<script>window.LIVEDEV_INITIAL_CATEGORY={json_module.dumps(category)};</script>'
        f'<script type="application/ld+json">{_safe_schema(schema)}</script>'
    )
    html = html.replace('</head>', f'{page_data}</head>', 1)
    response = HttpResponse(html, content_type='text/html; charset=utf-8')
    response['Cache-Control'] = 'public, max-age=300'
    return response


@require_GET
def service_index(request):
    return redirect('/', permanent=True)


@staff_member_required
def preview_showcase(request):
    """Старое общее превью — редирект на список карточек."""
    return redirect('admin:content_showcaseitem_changelist')


@staff_member_required
@require_http_methods(['GET', 'POST'])
def item_live_preview(request, pk=None, object_id=None):
    """
    Живое превью одной карточки: правишь текст справа — сразу видно слева.
    Сохранение пишет в БД и сбрасывает кэш витрины.
    """
    item_id = pk or object_id
    item = get_object_or_404(ShowcaseItem.objects.select_related('category'), pk=item_id)

    if request.method == 'POST':
        wants_json = 'application/json' in (request.headers.get('Accept') or '')
        try:
            if request.content_type and 'application/json' in request.content_type:
                body = json.loads(request.body.decode('utf-8') or '{}')
            else:
                body = request.POST
        except json.JSONDecodeError:
            return HttpResponseBadRequest('invalid json')

        title = (body.get('title') or '').strip()[:200]
        text = (body.get('text') or '').strip()
        points_raw = body.get('points')
        if isinstance(points_raw, list):
            points = [str(p).strip() for p in points_raw if str(p).strip()][:3]
        else:
            points = [
                line.strip()
                for line in str(points_raw or '').replace(',', '\n').splitlines()
                if line.strip()
            ][:3]

        if not title:
            if wants_json:
                return JsonResponse({'ok': False, 'error': 'title_required'}, status=400)
            messages.error(request, 'Заголовок обязателен')
            return redirect('admin:content_showcaseitem_live', object_id=item.pk)

        item.title = title
        item.text = text
        item.points = points
        item.save()
        if wants_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'ok': True,
                'item': {
                    'id': item.id,
                    'title': item.title,
                    'text': item.text,
                    'points': item.points,
                    'image': item.resolved_image,
                    'category_label': item.category.label,
                },
            })
        messages.success(request, 'Сохранено — на сайте обновится через /api/showcase/')
        return redirect('admin:content_showcaseitem_live', object_id=item.pk)

    return render(request, 'content/item_live_preview.html', {
        'title': f'Превью: {item.title}',
        'item': item,
        'image_url': item.resolved_image,
        'points_text': '\n'.join(item.points or []),
        'edit_url': f'/admin/content/showcaseitem/{item.pk}/change/',
    })
