from unfold.admin import ModelAdmin
from unfold.decorators import display

from analytics.models import PageVisit, PageEvent, ProductInterest
from analytics.views import visits_summary_context, interest_summary_context
from django.contrib import admin


@admin.register(PageVisit)
class PageVisitAdmin(ModelAdmin):
    change_list_template = 'admin/analytics/pagevisit_change_list.html'
    list_display = (
        'page_path', 'duration_human', 'geo_display', 'ip_address',
        'device', 'started_at',
    )
    list_filter = ('device', 'country', 'page_path')
    search_fields = ('page_path', 'ip_address', 'session_key', 'city', 'country')
    readonly_fields = [f.name for f in PageVisit._meta.fields]
    date_hierarchy = 'started_at'

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context.update(visits_summary_context(request))
        return super().changelist_view(request, extra_context=extra_context)

    @display(description='Время')
    def duration_human(self, obj):
        s = obj.duration_seconds or 0
        m, sec = divmod(s, 60)
        if m:
            return f'{m}м {sec}с'
        return f'{sec}с'

    @display(description='Гео')
    def geo_display(self, obj):
        if obj.city and obj.country:
            return f'{obj.city}, {obj.country}'
        if obj.country:
            return obj.country
        if obj.city:
            return obj.city
        ip = str(obj.ip_address or '')
        if ip.startswith(('127.', '10.', '192.168.', '::1')) or ip in ('', 'None'):
            return 'локально'
        return '—'


@admin.register(ProductInterest)
class ProductInterestAdmin(ModelAdmin):
    change_list_template = 'admin/analytics/interest_change_list.html'
    list_display = ('category_label', 'item_title', 'item_index', 'session_key_short', 'created_at')
    list_filter = ('category_slug', 'category_label')
    search_fields = ('item_title', 'category_label', 'session_key')
    readonly_fields = [f.name for f in ProductInterest._meta.fields]
    date_hierarchy = 'created_at'

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context.update(interest_summary_context(request))
        return super().changelist_view(request, extra_context=extra_context)

    @display(description='Сессия')
    def session_key_short(self, obj):
        s = obj.session_key or ''
        return f'{s[:8]}…' if len(s) > 10 else s


# Сырой журнал не в меню — оставляем только для отладки по прямому URL
@admin.register(PageEvent)
class PageEventAdmin(ModelAdmin):
    list_display = ('event_label', 'page_path', 'payload_short', 'created_at')
    list_filter = ('event_type',)
    search_fields = ('session_key', 'page_path')
    readonly_fields = [f.name for f in PageEvent._meta.fields]
    date_hierarchy = 'created_at'

    @display(description='Что произошло')
    def event_label(self, obj):
        return obj.get_event_type_display()

    @display(description='Детали')
    def payload_short(self, obj):
        p = obj.payload or {}
        if not p:
            return '—'
        if obj.event_type == PageEvent.EventType.SHOWCASE:
            return f"{p.get('category_label') or p.get('category') or ''} · {p.get('title') or ''}"
        if 'hash' in p:
            return p.get('hash')
        return str(p)[:80]
