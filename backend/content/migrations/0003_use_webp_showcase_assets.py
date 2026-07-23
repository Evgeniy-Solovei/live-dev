from django.db import migrations


def use_webp_assets(apps, schema_editor):
    ShowcaseItem = apps.get_model('content', 'ShowcaseItem')
    for item in ShowcaseItem.objects.filter(image_url__endswith='.png').iterator():
        if item.image_url.startswith(('assets/showcase/', '/assets/showcase/')):
            item.image_url = item.image_url[:-4] + '.webp'
            item.save(update_fields=['image_url'])


class Migration(migrations.Migration):
    dependencies = [('content', '0002_alter_showcasecategory_slug_and_more')]

    operations = [migrations.RunPython(use_webp_assets, migrations.RunPython.noop)]
