from django.db import models


class Lead(models.Model):
    class Status(models.TextChoices):
        NEW = 'new', 'Новая'
        IN_PROGRESS = 'in_progress', 'В работе'
        DONE = 'done', 'Закрыта'
        SPAM = 'spam', 'Спам'

    name = models.CharField('Имя', max_length=120)
    contact = models.CharField('Контакт', max_length=255, help_text='Telegram / телефон / email')
    message = models.TextField('Задача', blank=True, default='')
    status = models.CharField('Статус', max_length=20, choices=Status.choices, default=Status.NEW)
    source = models.CharField('Источник', max_length=64, default='site_form')
    page_url = models.CharField('Страница', max_length=500, blank=True, default='')
    ip_address = models.GenericIPAddressField('IP', null=True, blank=True)
    user_agent = models.TextField('User-Agent', blank=True, default='')
    country = models.CharField('Страна', max_length=64, blank=True, default='')
    city = models.CharField('Город', max_length=64, blank=True, default='')
    admin_note = models.TextField('Заметка', blank=True, default='')
    created_at = models.DateTimeField('Создана', auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'

    def __str__(self):
        return f'{self.name} · {self.contact}'
