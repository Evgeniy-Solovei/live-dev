from django.db import models


class PageVisit(models.Model):
    """Один заход посетителя на сайт (сессия + страница)."""

    session_key = models.CharField('Сессия', max_length=64, db_index=True)
    page_path = models.CharField('Страница / якорь', max_length=255, db_index=True)
    page_title = models.CharField('Title', max_length=255, blank=True, default='')
    referrer = models.CharField('Откуда пришёл', max_length=500, blank=True, default='')
    ip_address = models.GenericIPAddressField('IP', null=True, blank=True, db_index=True)
    country = models.CharField('Страна', max_length=64, blank=True, default='', db_index=True)
    country_code = models.CharField('Код страны', max_length=8, blank=True, default='')
    city = models.CharField('Город', max_length=64, blank=True, default='')
    user_agent = models.TextField('User-Agent', blank=True, default='')
    device = models.CharField('Устройство', max_length=32, blank=True, default='')
    started_at = models.DateTimeField('Начало', auto_now_add=True, db_index=True)
    last_seen_at = models.DateTimeField('Последний ping', auto_now=True)
    duration_seconds = models.PositiveIntegerField('Секунд на странице', default=0)
    is_bounce = models.BooleanField('Отказ (<15 сек)', default=True)

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Визит'
        verbose_name_plural = 'Визиты'
        indexes = [
            models.Index(fields=['page_path', '-started_at']),
            models.Index(fields=['country', '-started_at']),
        ]

    def __str__(self):
        geo = self.city or self.country or 'без гео'
        return f'{self.page_path} · {self.duration_seconds}s · {geo}'


class PageEvent(models.Model):
    """
    Служебный журнал сырых сигналов с сайта (просмотр, уход, клик по якорю).
    Для бизнеса смотрите «Интерес к продуктам» и сводку визитов — не этот список.
    """

    class EventType(models.TextChoices):
        VIEW = 'view', 'Открыл страницу'
        HEARTBEAT = 'heartbeat', 'На сайте (пинг)'
        LEAVE = 'leave', 'Ушёл со страницы'
        CLICK = 'click', 'Клик'
        SECTION = 'section', 'Перешёл к секции'
        SHOWCASE = 'showcase', 'Смотрел витрину'

    visit = models.ForeignKey(
        PageVisit,
        on_delete=models.CASCADE,
        related_name='events',
        null=True,
        blank=True,
        verbose_name='Визит',
    )
    session_key = models.CharField('Сессия', max_length=64, db_index=True, blank=True, default='')
    event_type = models.CharField('Тип', max_length=32, choices=EventType.choices, db_index=True)
    page_path = models.CharField('Страница', max_length=255, blank=True, default='')
    payload = models.JSONField('Детали', default=dict, blank=True)
    created_at = models.DateTimeField('Когда', auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Сырое событие'
        verbose_name_plural = 'Сырые события (журнал)'

    def __str__(self):
        return f'{self.get_event_type_display()} · {self.page_path}'


class ProductInterest(models.Model):
    """Что смотрели в витрине: CRM / боты / лендинги / …"""

    session_key = models.CharField('Сессия', max_length=64, db_index=True)
    visit = models.ForeignKey(
        PageVisit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='product_interests',
        verbose_name='Визит',
    )
    category_slug = models.SlugField('Раздел (ключ)', max_length=64, db_index=True)
    category_label = models.CharField('Раздел', max_length=120, blank=True, default='')
    item_title = models.CharField('Проект', max_length=200, blank=True, default='')
    item_index = models.PositiveIntegerField('№ в карусели', default=0)
    created_at = models.DateTimeField('Когда', auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Интерес к продукту'
        verbose_name_plural = 'Интерес к продуктам'
        indexes = [
            models.Index(fields=['category_slug', '-created_at']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f'{self.category_label or self.category_slug}: {self.item_title}'
