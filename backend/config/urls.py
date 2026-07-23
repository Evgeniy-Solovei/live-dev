from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

from content.views import (
    public_showcase,
    preview_showcase,
    item_live_preview,
    service_index,
    service_detail,
)
from leads.views import create_lead
from analytics.views import track_beacon
from core.views import public_settings, home, frontend_root_file, privacy, sitemap

urlpatterns = [
    path('', home, name='home'),
    path('sw.js', frontend_root_file, {'name': 'sw.js'}, name='sw_js'),
    path('build.json', frontend_root_file, {'name': 'build.json'}, name='build_json'),
    path('robots.txt', frontend_root_file, {'name': 'robots.txt'}, name='robots_txt'),
    path('sitemap.xml', sitemap, name='sitemap_xml'),
    path('privacy/', privacy, name='privacy'),
    path('uslugi/', service_index, name='service_index'),
    path('uslugi/<slug:slug>/', service_detail, name='service_detail'),
    # Старый URL превью → редирект; живое превью также в admin get_urls
    path('admin/content/preview/', preview_showcase, name='showcase_preview'),
    path(
        'admin/content/showcaseitem/<int:pk>/live/',
        item_live_preview,
        name='item_live_preview',
    ),
    path('admin/', admin.site.urls),
    path('api/showcase/', public_showcase, name='api_showcase'),
    path('api/settings/', public_settings, name='api_settings'),
    path('api/leads/', create_lead, name='api_leads'),
    path('api/analytics/beacon/', track_beacon, name='api_analytics_beacon'),
    # Статика сайта и витрины (управляется через админку + seed)
    path(
        'assets/<path:path>',
        serve,
        {'document_root': settings.FRONTEND_DIR / 'assets'},
    ),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
