import json
import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.utils import allow_request, client_ip, lookup_geo
from core.views import notify_telegram
from core.models import SiteSettings
from leads.models import Lead


logger = logging.getLogger(__name__)


def notify_email(lead, geo_line):
    """Send a lead copy to the public contact email without blocking lead creation on failure."""
    recipient = (SiteSettings.load().contact_email or '').strip()
    if not settings.EMAIL_NOTIFICATIONS_ENABLED or not recipient:
        return {'ok': False, 'skipped': True}
    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        logger.warning('Lead email is enabled, but SMTP credentials are missing')
        return {'ok': False, 'skipped': True}

    reply_to = []
    try:
        validate_email(lead.contact)
        reply_to = [lead.contact]
    except ValidationError:
        pass

    body = (
        f'Новая заявка LiveDev №{lead.id}\n\n'
        f'Имя: {lead.name}\n'
        f'Контакт: {lead.contact}\n'
        f'Задача: {lead.message or "—"}\n\n'
        f'Страница: {lead.page_url or "/"}\n'
        f'География: {geo_line}\n'
        f'IP: {lead.ip_address or "—"}\n'
        f'Источник: {lead.source}\n'
    )
    try:
        sent = EmailMessage(
            subject=f'Новая заявка LiveDev №{lead.id}: {lead.name}',
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
            reply_to=reply_to,
        ).send(fail_silently=False)
        return {'ok': bool(sent), 'skipped': False}
    except Exception:
        logger.exception('Could not send lead %s email notification', lead.id)
        return {'ok': False, 'skipped': False}


@csrf_exempt
@require_POST
def create_lead(request):
    ip = client_ip(request)
    if not allow_request('lead', ip or 'unknown', settings.LEAD_RATE_LIMIT):
        return JsonResponse({'ok': False, 'error': 'too_many_requests'}, status=429)

    try:
        body = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return HttpResponseBadRequest('invalid json')

    if not isinstance(body, dict):
        return JsonResponse({'ok': False, 'error': 'invalid_payload'}, status=400)

    # Hidden field: browsers leave it blank, simple spambots usually fill it.
    if body.get('company_website'):
        return JsonResponse({'ok': True})

    name = str(body.get('name') or '').strip()
    contact = str(body.get('contact') or '').strip()
    message = str(body.get('message') or '').strip()
    if not name or not contact:
        return JsonResponse({'ok': False, 'error': 'name_and_contact_required'}, status=400)

    geo = lookup_geo(ip)
    ua = request.META.get('HTTP_USER_AGENT', '')[:1000]

    lead = Lead.objects.create(
        name=name[:120],
        contact=contact[:255],
        message=message[:5000],
        source=str(body.get('source') or 'site_form')[:64],
        page_url=str(body.get('page_url') or '')[:500],
        ip_address=ip,
        user_agent=ua,
        country=geo.get('country', ''),
        city=geo.get('city', ''),
    )

    geo_line = ', '.join(x for x in [lead.city, lead.country] if x) or '—'
    tg = notify_telegram(
        '🆕 Новая заявка LiveDev\n'
        f'👤 {lead.name}\n'
        f'📞 {lead.contact}\n'
        f'💬 {lead.message or "—"}\n'
        f'🌐 {lead.page_url or "/"}\n'
        f'📍 {geo_line} · IP {lead.ip_address or "—"}\n'
        f'🏷 {lead.source}'
    )
    email = notify_email(lead, geo_line)
    return JsonResponse({
        'ok': True,
        'id': lead.id,
        'telegram': tg.get('ok', False),
        'email': email.get('ok', False),
    })
