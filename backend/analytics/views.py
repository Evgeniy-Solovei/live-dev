"""Analytics beacon API + helpers for admin summary blocks."""
import json
import re
from datetime import datetime, time, timedelta

from django.conf import settings
from django.core.cache import cache
from django.db.models import Avg, Count, Q
from django.db.models.functions import TruncDate
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from analytics.models import PageVisit, PageEvent, ProductInterest
from core.models import SiteSettings
from core.utils import allow_request, client_ip, lookup_geo, detect_device


def parse_date_range(request):
    """Return (date_from, date_to) inclusive. Default: last 30 days."""
    today = timezone.localdate()
    raw_from = (request.GET.get('from') or '').strip()
    raw_to = (request.GET.get('to') or '').strip()
    try:
        date_to = datetime.strptime(raw_to, '%Y-%m-%d').date() if raw_to else today
    except ValueError:
        date_to = today
    try:
        date_from = datetime.strptime(raw_from, '%Y-%m-%d').date() if raw_from else date_to - timedelta(days=29)
    except ValueError:
        date_from = date_to - timedelta(days=29)
    if date_from > date_to:
        date_from, date_to = date_to, date_from
    return date_from, date_to


def aware_range(date_from, date_to):
    tz = timezone.get_current_timezone()
    start = timezone.make_aware(datetime.combine(date_from, time.min), tz)
    end = timezone.make_aware(datetime.combine(date_to, time.max), tz)
    return start, end


def visits_summary_context(request):
    date_from, date_to = parse_date_range(request)
    start, end = aware_range(date_from, date_to)
    qs = PageVisit.objects.filter(started_at__gte=start, started_at__lte=end)

    total = qs.count()
    unique_sessions = qs.values('session_key').distinct().count()
    avg_duration = qs.aggregate(v=Avg('duration_seconds'))['v'] or 0

    by_day = list(
        qs.annotate(day=TruncDate('started_at'))
        .values('day')
        .annotate(
            visits=Count('id'),
            sessions=Count('session_key', distinct=True),
            avg_sec=Avg('duration_seconds'),
        )
        .order_by('day')
    )
    by_country = list(
        qs.exclude(country='')
        .values('country')
        .annotate(visits=Count('id'))
        .order_by('-visits')[:12]
    )
    no_geo = qs.filter(Q(country='') | Q(country__isnull=True)).count()
    by_device = list(qs.values('device').annotate(visits=Count('id')).order_by('-visits'))
    by_path = list(
        qs.values('page_path').annotate(visits=Count('id')).order_by('-visits')[:10]
    )

    interest_qs = ProductInterest.objects.filter(created_at__gte=start, created_at__lte=end)
    by_category = list(
        interest_qs.values('category_slug', 'category_label')
        .annotate(views=Count('id'), sessions=Count('session_key', distinct=True))
        .order_by('-views')
    )

    return {
        'summary_date_from': date_from.isoformat(),
        'summary_date_to': date_to.isoformat(),
        'summary_total': total,
        'summary_unique_sessions': unique_sessions,
        'summary_avg_duration': int(avg_duration),
        'summary_by_day': by_day,
        'summary_by_country': by_country,
        'summary_no_geo': no_geo,
        'summary_by_device': by_device,
        'summary_by_path': by_path,
        'summary_by_category': by_category,
        'summary_interest_total': interest_qs.count(),
    }


def interest_summary_context(request):
    date_from, date_to = parse_date_range(request)
    start, end = aware_range(date_from, date_to)
    qs = ProductInterest.objects.filter(created_at__gte=start, created_at__lte=end)

    by_category = list(
        qs.values('category_slug', 'category_label')
        .annotate(views=Count('id'), sessions=Count('session_key', distinct=True))
        .order_by('-views')
    )
    by_item = list(
        qs.values('category_label', 'item_title')
        .annotate(views=Count('id'))
        .order_by('-views')[:25]
    )
    by_day = list(
        qs.annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(views=Count('id'))
        .order_by('day')
    )

    return {
        'summary_date_from': date_from.isoformat(),
        'summary_date_to': date_to.isoformat(),
        'summary_total': qs.count(),
        'summary_by_category': by_category,
        'summary_by_item': by_item,
        'summary_by_day': by_day,
    }


@csrf_exempt
@require_POST
def track_beacon(request):
    settings_obj = SiteSettings.load()
    if not settings_obj.analytics_enabled:
        return JsonResponse({'ok': True, 'disabled': True})

    ip = client_ip(request)
    if not allow_request('analytics', ip or 'unknown', settings.ANALYTICS_RATE_LIMIT):
        return JsonResponse({'ok': False, 'error': 'too_many_requests'}, status=429)

    try:
        body = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return HttpResponseBadRequest('invalid json')

    if not isinstance(body, dict):
        return JsonResponse({'ok': False, 'error': 'invalid_payload'}, status=400)

    event_type = str(body.get('event') or 'view').strip()
    session_key = str(body.get('session') or '')[:64]
    page_path = str(body.get('path') or '/')[:255]
    page_title = str(body.get('title') or '')[:255]
    referrer = str(body.get('referrer') or '')[:500]
    try:
        duration = max(0, min(int(body.get('duration') or 0), 86400))
    except (TypeError, ValueError):
        duration = 0
    visit_id = body.get('visit_id')
    payload = body.get('payload') or {}
    if not isinstance(payload, dict):
        payload = {}
    if len(json.dumps(payload, ensure_ascii=False)) > 4096:
        payload = {}

    if not re.fullmatch(r'[A-Za-z0-9-]{16,64}', session_key):
        return JsonResponse({'ok': False, 'error': 'session_required'}, status=400)

    allowed_events = {'view', 'heartbeat', 'leave', 'click', 'section', 'showcase'}
    if event_type not in allowed_events:
        return JsonResponse({'ok': False, 'error': 'invalid_event'}, status=400)

    ua = request.META.get('HTTP_USER_AGENT', '')[:1000]
    visit = None

    if visit_id:
        visit = PageVisit.objects.filter(id=visit_id, session_key=session_key).first()

    if event_type == 'view' or visit is None:
        geo = lookup_geo(ip)
        visit = PageVisit.objects.create(
            session_key=session_key,
            page_path=page_path,
            page_title=page_title,
            referrer=referrer,
            ip_address=ip,
            country=geo.get('country', ''),
            country_code=geo.get('country_code', ''),
            city=geo.get('city', ''),
            user_agent=ua,
            device=detect_device(ua),
            duration_seconds=max(0, duration),
            is_bounce=True,
        )
        PageEvent.objects.create(
            visit=visit,
            session_key=session_key,
            event_type=PageEvent.EventType.VIEW,
            page_path=page_path,
            payload={'title': page_title},
        )
        return JsonResponse({'ok': True, 'visit_id': visit.id})

    if duration > visit.duration_seconds:
        visit.duration_seconds = duration
    visit.last_seen_at = timezone.now()
    if visit.duration_seconds >= 15:
        visit.is_bounce = False
    if page_path and page_path != visit.page_path and event_type == 'section':
        visit.page_path = page_path

    if ip and not visit.country:
        geo = lookup_geo(ip)
        if geo.get('country'):
            visit.country = geo['country']
            visit.country_code = geo.get('country_code', '')
            visit.city = geo.get('city', '')
            if not visit.ip_address:
                visit.ip_address = ip

    visit.save()

    if event_type == 'showcase':
        cat = str(payload.get('category') or payload.get('category_slug') or '')[:64]
        label = str(payload.get('category_label') or payload.get('label') or '')[:120]
        title = str(payload.get('title') or payload.get('item_title') or '')[:200]
        try:
            idx = int(payload.get('index') or payload.get('item_index') or 0)
        except (TypeError, ValueError):
            idx = 0
        if cat:
            interest_key = f'interest:{visit.id}:{cat}:{idx}'
            if cache.add(interest_key, 1, 15):
                ProductInterest.objects.create(
                    session_key=session_key,
                    visit=visit,
                    category_slug=cat,
                    category_label=label or cat,
                    item_title=title,
                    item_index=max(0, idx),
                )
            PageEvent.objects.create(
                visit=visit,
                session_key=session_key,
                event_type=PageEvent.EventType.SHOWCASE,
                page_path=page_path,
                payload=payload,
            )
        return JsonResponse({'ok': True, 'visit_id': visit.id})

    mapped = {
        'heartbeat': PageEvent.EventType.HEARTBEAT,
        'leave': PageEvent.EventType.LEAVE,
        'click': PageEvent.EventType.CLICK,
        'section': PageEvent.EventType.SECTION,
    }.get(event_type, PageEvent.EventType.HEARTBEAT)

    if event_type != 'heartbeat':
        PageEvent.objects.create(
            visit=visit,
            session_key=session_key,
            event_type=mapped,
            page_path=page_path,
            payload=payload,
        )

    return JsonResponse({'ok': True, 'visit_id': visit.id, 'duration': visit.duration_seconds})
