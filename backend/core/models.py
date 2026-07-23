from django.db import models


class SiteSettings(models.Model):
    """Singleton: contacts, ads counters, Telegram alerts."""

    site_name = models.CharField('Название сайта', max_length=120, default='LiveDev')
    contact_email = models.EmailField('Email', default='live-dev@mail.ru')
    contact_phone = models.CharField('Телефон', max_length=64, default='+375 29 894-54-62')
    contact_telegram = models.CharField('Telegram', max_length=64, default='@solovey_ev')

    telegram_bot_token = models.CharField(
        'Токен бота (@BotFather)',
        max_length=128,
        blank=True,
        default='',
        help_text='Создай бота у @BotFather → вставь токен сюда. Потом напиши боту /start и нажми «Подключить бота».',
    )
    telegram_chat_id = models.CharField(
        'Куда слать (подставится само)',
        max_length=64,
        blank=True,
        default='',
        help_text='Не надо искать вручную: напиши боту /start → кнопка «Подключить бота». '
                  'Это просто адрес твоего Telegram, иначе бот не знает, кому писать.',
    )

    yandex_metrika_id = models.CharField(
        'Яндекс.Метрика ID',
        max_length=32,
        blank=True,
        default='',
        help_text='Числовой ID счётчика с metrika.yandex.ru',
    )
    yandex_metrika_webvisor = models.BooleanField('Метрика: вебвизор', default=True)
    yandex_goal_name = models.CharField(
        'Цель заявки в Яндекс.Метрике',
        max_length=128,
        blank=True,
        default='lead_submit',
        help_text='Имя цели из Метрики. По умолчанию: lead_submit.',
    )
    yandex_ads_enabled = models.BooleanField('Включить скрипты Яндекс.Рекламы (РСЯ)', default=False)
    yandex_ads_block_id = models.CharField(
        'ID рекламного блока РСЯ',
        max_length=64,
        blank=True,
        default='',
        help_text='Только если показываете баннеры РСЯ на своём сайте.',
    )

    google_analytics_id = models.CharField(
        'Google Analytics 4 (G-XXXX)',
        max_length=32,
        blank=True,
        default='',
        help_text='Measurement ID из analytics.google.com',
    )
    google_ads_id = models.CharField(
        'Google Ads (AW-XXXX)',
        max_length=32,
        blank=True,
        default='',
        help_text='Когда запускаете Google Ads.',
    )
    google_ads_conversion_label = models.CharField(
        'Google Ads Conversion Label',
        max_length=64,
        blank=True,
        default='',
        help_text='Метка конверсии из действия-конверсии Google Ads.',
    )
    google_tag_manager_id = models.CharField(
        'Google Tag Manager (GTM-XXXX)',
        max_length=32,
        blank=True,
        default='',
    )

    analytics_enabled = models.BooleanField('Своя аналитика LiveDev (визиты / интерес)', default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Контакты и счётчики'
        verbose_name_plural = 'Контакты и счётчики'

    def __str__(self):
        return 'Контакты и счётчики'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        from django.core.cache import cache
        cache.delete('public_site_settings')

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
