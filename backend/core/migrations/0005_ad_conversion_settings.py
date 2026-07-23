from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('core', '0004_telegram_labels')]

    operations = [
        migrations.RenameField(
            model_name='sitesettings',
            old_name='yandex_direct_counter',
            new_name='yandex_goal_name',
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='yandex_goal_name',
            field=models.CharField(
                blank=True,
                default='lead_submit',
                help_text='Имя цели из Метрики. По умолчанию: lead_submit.',
                max_length=128,
                verbose_name='Цель заявки в Яндекс.Метрике',
            ),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='google_ads_conversion_label',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Метка конверсии из действия-конверсии Google Ads.',
                max_length=64,
                verbose_name='Google Ads Conversion Label',
            ),
        ),
    ]
