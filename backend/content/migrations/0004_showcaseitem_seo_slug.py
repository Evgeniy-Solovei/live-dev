from django.db import migrations, models


TRANSLIT = str.maketrans({
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'h', 'ц': 'c', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
})


def fill_slugs(apps, schema_editor):
    from django.utils.text import slugify

    ShowcaseItem = apps.get_model('content', 'ShowcaseItem')
    used = set()
    for item in ShowcaseItem.objects.order_by('id'):
        base = slugify(item.title.lower().translate(TRANSLIT))[:220] or f'project-{item.pk}'
        candidate = base
        number = 2
        while candidate in used:
            candidate = f'{base}-{number}'
            number += 1
        item.seo_slug = candidate
        item.save(update_fields=['seo_slug'])
        used.add(candidate)


class Migration(migrations.Migration):
    dependencies = [('content', '0003_use_webp_showcase_assets')]

    operations = [
        migrations.AddField(
            model_name='showcaseitem',
            name='seo_slug',
            field=models.SlugField(
                blank=True,
                help_text='Заполняется автоматически, например crm-dlya-salona.',
                max_length=240,
                null=True,
                unique=True,
                verbose_name='URL страницы примера',
            ),
        ),
        migrations.RunPython(fill_slugs, migrations.RunPython.noop),
    ]
