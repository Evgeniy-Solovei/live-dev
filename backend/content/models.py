from io import BytesIO

from django.core.cache import cache
from django.core.files.base import ContentFile
from django.db import models
from PIL import Image


TRANSLIT = str.maketrans({
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'h', 'ц': 'c', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
})


def seo_slugify(value: str) -> str:
    from django.utils.text import slugify

    return slugify((value or '').lower().translate(TRANSLIT))[:220] or 'project'


class ShowcaseCategory(models.Model):
    slug = models.SlugField(
        'Ключ раздела',
        max_length=64,
        unique=True,
        help_text='crm, telegram, shop, ai, bots, vpn, landings…',
    )
    label = models.CharField('Название в интерфейсе', max_length=120)
    sort_order = models.PositiveIntegerField('Порядок', default=0)
    is_active = models.BooleanField('Показывать на сайте', default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'id']
        verbose_name = 'Раздел витрины'
        verbose_name_plural = 'Разделы витрины'

    def __str__(self):
        return self.label

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        cache.delete('public_showcase')

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        cache.delete('public_showcase')


def _optimize_upload_to_webp(uploaded_file):
    """Encode upload as high-quality WebP. Max 2400×1350, never upscale."""
    uploaded_file.seek(0)
    im = Image.open(uploaded_file).convert('RGB')
    max_w, max_h = 2400, 1350
    if im.width > max_w or im.height > max_h:
        scale = min(max_w / im.width, max_h / im.height)
        nw, nh = int(im.width * scale + 0.5), int(im.height * scale + 0.5)
        im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    buf = BytesIO()
    # Quality 94 preserves small UI text while being much smaller than PNG.
    im.save(buf, format='WEBP', quality=94, method=6)
    return ContentFile(buf.getvalue())


class ShowcaseItem(models.Model):
    category = models.ForeignKey(
        ShowcaseCategory,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Раздел',
    )
    title = models.CharField('Заголовок', max_length=200)
    seo_slug = models.SlugField(
        'URL страницы примера',
        max_length=240,
        unique=True,
        null=True,
        blank=True,
        help_text='Заполняется автоматически, например crm-dlya-salona.',
    )
    text = models.TextField('Описание')
    points = models.JSONField(
        'Теги / пункты',
        default=list,
        blank=True,
        help_text='Список строк — плашки под описанием',
    )
    image = models.ImageField('Картинка', upload_to='showcase/%Y/%m/', blank=True)
    image_url = models.CharField(
        'Или путь к уже лежащему файлу',
        max_length=500,
        blank=True,
        default='',
        help_text='Например assets/showcase/crm-1.webp — файл из папки фронта',
    )
    sort_order = models.PositiveIntegerField('Порядок', default=0)
    is_active = models.BooleanField('Показывать', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'id']
        verbose_name = 'Карточка проекта'
        verbose_name_plural = 'Карточки проектов'

    def __str__(self):
        return self.title

    @property
    def resolved_image(self):
        if self.image:
            return self.image.url
        url = (self.image_url or '').strip()
        if not url:
            return ''
        # Always root-absolute so admin at /admin/... doesn't treat path as object ID
        if url.startswith(('http://', 'https://', '/')):
            return url
        return f'/{url.lstrip("./")}'

    def save(self, *args, **kwargs):
        if not self.seo_slug:
            base = seo_slugify(self.title)
            candidate = base
            number = 2
            while ShowcaseItem.objects.exclude(pk=self.pk).filter(seo_slug=candidate).exists():
                candidate = f'{base}-{number}'
                number += 1
            self.seo_slug = candidate

        if isinstance(self.points, str):
            self.points = [
                p.strip()
                for p in self.points.replace(',', '\n').splitlines()
                if p.strip()
            ]

        img_name = (getattr(self.image, 'name', '') or '').lower()
        if self.image and hasattr(self.image, 'file') and not img_name.endswith('.webp'):
            try:
                raw = self.image
                optimized = _optimize_upload_to_webp(raw)
                base = (raw.name or 'showcase').rsplit('/', 1)[-1].rsplit('.', 1)[0]
                self.image.save(f'{base}.webp', optimized, save=False)
            except (OSError, ValueError):
                # ImageField validation still reports invalid uploads in admin.
                pass

        super().save(*args, **kwargs)
        cache.delete('public_showcase')

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        cache.delete('public_showcase')
