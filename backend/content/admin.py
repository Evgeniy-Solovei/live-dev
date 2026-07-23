from django import forms
from django.contrib import admin
from django.urls import path, reverse
from django.utils.html import format_html, format_html_join
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display

from content.models import ShowcaseCategory, ShowcaseItem
from content.views import item_live_preview


class PointsListField(forms.CharField):
    """Один тег на строку — удобнее, чем сырой JSON."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            'widget',
            forms.Textarea(attrs={'rows': 4, 'placeholder': 'складской учёт\nзаправка\nаттестация'}),
        )
        kwargs.setdefault('required', False)
        super().__init__(*args, **kwargs)

    def prepare_value(self, value):
        if isinstance(value, list):
            return '\n'.join(str(v) for v in value)
        if isinstance(value, str):
            return value
        return ''

    def to_python(self, value):
        if not value:
            return []
        if isinstance(value, list):
            return value
        return [line.strip() for line in str(value).replace(',', '\n').splitlines() if line.strip()]


class ShowcaseItemAdminForm(forms.ModelForm):
    points = PointsListField(
        label='Теги / пункты',
        help_text='По одному тегу на строку (на сайте показываем максимум 3).',
    )

    class Meta:
        model = ShowcaseItem
        fields = '__all__'


class ShowcaseItemInline(TabularInline):
    model = ShowcaseItem
    extra = 0
    fields = ('title', 'image', 'image_url', 'sort_order', 'is_active')
    show_change_link = True
    tab = True


@admin.register(ShowcaseCategory)
class ShowcaseCategoryAdmin(ModelAdmin):
    list_display = ('label', 'slug', 'sort_order', 'is_active', 'items_count')
    list_editable = ('sort_order', 'is_active')
    search_fields = ('label', 'slug')
    prepopulated_fields = {'slug': ('label',)}
    inlines = [ShowcaseItemInline]

    @display(description='Карточек')
    def items_count(self, obj):
        return obj.items.count()


@admin.register(ShowcaseItem)
class ShowcaseItemAdmin(ModelAdmin):
    form = ShowcaseItemAdminForm
    list_display = ('thumb', 'title', 'category', 'live_link', 'sort_order', 'is_active', 'updated_at')
    list_display_links = ('title',)
    list_filter = ('category', 'is_active')
    list_editable = ('sort_order', 'is_active')
    search_fields = ('title', 'seo_slug', 'text')
    list_select_related = ('category',)
    autocomplete_fields = ('category',)
    readonly_fields = ('card_preview', 'live_link_help', 'public_page_link')
    fieldsets = (
        ('Как будет на сайте', {
            'fields': ('card_preview', 'live_link_help', 'public_page_link'),
            'description': 'Превью = фото + заголовок + описание + теги. '
                           'Обновляется, пока печатаешь поля ниже — видно, как длинный текст влияет на карточку.',
        }),
        ('Раздел', {'fields': ('category', 'sort_order', 'is_active')}),
        ('Текст на сайте', {
            'fields': ('title', 'seo_slug', 'text', 'points'),
        }),
        ('Картинка', {
            'fields': ('image', 'image_url'),
            'description': 'Файл в media или путь assets/showcase/…. На сайте без обрезки (fill).',
        }),
    )

    class Media:
        css = {'all': ('admin/showcase_preview.css',)}
        js = ('admin/showcase_preview.js',)

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                '<path:object_id>/live/',
                self.admin_site.admin_view(item_live_preview),
                name='content_showcaseitem_live',
            ),
        ]
        return custom + urls

    @display(description='Миниатюра')
    def thumb(self, obj):
        url = obj.resolved_image
        if not url:
            return '—'
        return format_html(
            '<img src="{}" style="height:40px;width:72px;object-fit:fill;border-radius:6px;background:#111;" />',
            url,
        )

    @display(description='Превью')
    def live_link(self, obj):
        if not obj.pk:
            return '—'
        url = reverse('admin:content_showcaseitem_live', args=[obj.pk])
        return format_html('<a href="{}">Смотреть / править</a>', url)

    @display(description='Отдельная страница')
    def live_link_help(self, obj):
        if not obj.pk:
            return 'Сначала сохраните карточку.'
        url = reverse('admin:content_showcaseitem_live', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}" target="_blank" rel="noopener">'
            'Открыть на весь экран (удобнее править текст)</a>',
            url,
        )

    @display(description='SEO-страница проекта')
    def public_page_link(self, obj):
        if not obj or not obj.pk or not obj.seo_slug:
            return 'Появится после сохранения карточки.'
        url = reverse('portfolio_detail', args=[obj.seo_slug])
        return format_html('<a href="{}" target="_blank" rel="noopener">Открыть публичную страницу</a>', url)

    @display(description='Превью карточки')
    def card_preview(self, obj):
        cat = obj.category.label if obj and obj.category_id else 'Раздел'
        title = obj.title if obj else ''
        text = obj.text if obj else ''
        points = (obj.points or [])[:3] if obj else []
        img = obj.resolved_image if obj else ''

        points_html = format_html_join('', '<span>{}</span>', ((p,) for p in points))
        if img:
            img_html = format_html('<img src="{}" alt="">', img)
        else:
            img_html = format_html('<div class="ld-pv-empty">Нет картинки</div>')

        return format_html(
            '<div class="ld-pv" id="ld-card-preview">'
            '<div class="ld-pv-stage">'
            '<div class="ld-pv-visual">{}</div>'
            '<div class="ld-pv-copy">'
            '<div class="ld-pv-kicker" data-pv="cat">{}</div>'
            '<h3 data-pv="title">{}</h3>'
            '<p data-pv="text">{}</p>'
            '<div class="ld-pv-points" data-pv="points">{}</div>'
            '<div class="ld-pv-bottom"><span>превью текста + фото</span><span>← →</span></div>'
            '</div></div>'
            '<p class="ld-pv-hint">Меняй «Заголовок / Описание / Теги» ниже — превью обновится сразу.</p>'
            '</div>',
            img_html,
            cat,
            title,
            text,
            points_html,
        )
