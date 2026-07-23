from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path
from django.utils.html import format_html
from unfold.admin import ModelAdmin

from core.models import SiteSettings
from core.views import discover_telegram_chat, notify_telegram


@admin.register(SiteSettings)
class SiteSettingsAdmin(ModelAdmin):
    fieldsets = (
        ('Контакты на сайте', {
            'fields': ('site_name', 'contact_email', 'contact_phone', 'contact_telegram'),
            'description': 'Показываются посетителям (футер / формы).',
        }),
        ('Telegram-бот для заявок', {
            'fields': ('telegram_bot_token', 'telegram_actions'),
            'description': (
                '1) @BotFather → создай бота → вставь токен сюда и сохрани. '
                '2) Открой бота в Telegram → /start. '
                '3) Жми «Подключить» — заявки начнут приходить в этот бот.'
            ),
        }),
        ('Яндекс.Метрика (аналитика трафика)', {
            'fields': (
                'yandex_metrika_id',
                'yandex_metrika_webvisor',
            ),
            'description': 'Счётчик на metrika.yandex.ru → ID сюда. Это статистика, не реклама.',
        }),
        ('Яндекс.Директ (цель заявки)', {
            'fields': ('yandex_goal_name',),
            'description': 'Создайте в Метрике JavaScript-событие lead_submit и оставьте это имя здесь.',
        }),
        ('Google (опционально)', {
            'fields': (
                'google_analytics_id',
                'google_tag_manager_id',
                'google_ads_id',
                'google_ads_conversion_label',
            ),
            'description': (
                'Простой вариант: GA4 + Google Ads ID/Label, GTM оставить пустым. '
                'Если используете GTM, управляйте тегами внутри него и не дублируйте прямые идентификаторы.'
            ),
        }),
        ('Своя аналитика LiveDev', {
            'fields': ('analytics_enabled',),
        }),
    )
    readonly_fields = ('telegram_actions',)

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                'connect-telegram/',
                self.admin_site.admin_view(self.connect_telegram),
                name='core_sitesettings_connect_telegram',
            ),
            path(
                'test-telegram/',
                self.admin_site.admin_view(self.test_telegram),
                name='core_sitesettings_test_telegram',
            ),
        ]
        return custom + urls

    def telegram_actions(self, obj=None):
        s = obj or SiteSettings.load()
        status = (
            format_html('<span style="color:#3dd68c;font-weight:700;">бот подключён</span>')
            if (s and s.telegram_chat_id and s.telegram_bot_token)
            else format_html('<span style="opacity:.7;">ещё не подключён</span>')
        )
        return format_html(
            '<p style="margin:0 0 10px;">Статус: {}</p>'
            '<div style="display:flex;flex-wrap:wrap;gap:10px;">'
            '<a class="button" href="{}">Подключить бота</a>'
            '<a class="button" href="{}">Отправить тест</a>'
            '</div>',
            status,
            '/admin/core/sitesettings/connect-telegram/',
            '/admin/core/sitesettings/test-telegram/',
        )
    telegram_actions.short_description = ' '

    def connect_telegram(self, request):
        s = SiteSettings.load()
        if not (s.telegram_bot_token or '').strip():
            messages.error(request, 'Сначала вставь токен бота и нажми «Сохранить».')
            return redirect('admin:core_sitesettings_change', object_id=1)

        found = discover_telegram_chat()
        if not found.get('ok'):
            messages.error(request, found.get('error') or 'Не удалось подключить')
            return redirect('admin:core_sitesettings_change', object_id=1)

        test = notify_telegram('✅ LiveDev: бот подключён.\nЗаявки с сайта будут приходить сюда.')
        if test.get('ok'):
            messages.success(request, 'Готово. Проверь бота в Telegram — должно прийти сообщение.')
        else:
            messages.warning(request, f'Подключили, но тест не ушёл: {test.get("error")}')
        return redirect('admin:core_sitesettings_change', object_id=1)

    def test_telegram(self, request):
        result = notify_telegram('✅ LiveDev: тест заявки\nЕсли видишь это — всё ок.')
        if result.get('ok'):
            messages.success(request, 'Тест ушёл в бота.')
        else:
            messages.error(request, result.get('error') or 'Ошибка')
        return redirect('admin:core_sitesettings_change', object_id=1)

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
