"""Загрузить fixtures/initial_content.json (пусто → первый деплой; --replace → перезалить витрину)."""
import json
from pathlib import Path

from django.core.management import BaseCommand, call_command
from django.core.cache import cache

from content.models import ShowcaseCategory, ShowcaseItem
from core.models import SiteSettings


class Command(BaseCommand):
    help = 'Загрузка initial_content.json в БД'

    def add_arguments(self, parser):
        parser.add_argument(
            '--replace',
            action='store_true',
            help='Очистить витрину и залить заново',
        )
        parser.add_argument(
            '--path',
            default='fixtures/initial_content.json',
            help='Путь к JSON-дампу',
        )

    def handle(self, *args, **options):
        path = Path(options['path'])
        if not path.is_file():
            self.stderr.write(self.style.ERROR(f'No fixture: {path}'))
            raise SystemExit(1)

        if ShowcaseItem.objects.exists() and not options['replace']:
            self.stdout.write('Showcase already has data — skip')
            return

        if options['replace']:
            ShowcaseItem.objects.all().delete()
            ShowcaseCategory.objects.all().delete()
            self.stdout.write('Cleared showcase')

        # Категории + карточки через loaddata (pk как в дампе)
        # SiteSettings — отдельно, т.к. singleton уже может существовать
        data = json.loads(path.read_text(encoding='utf-8'))
        content_only = [o for o in data if o['model'].startswith('content.')]
        settings_objs = [o for o in data if o['model'] == 'core.sitesettings']

        tmp = path.parent / '_content_only.json'
        tmp.write_text(json.dumps(content_only, ensure_ascii=False, indent=2), encoding='utf-8')
        try:
            call_command('loaddata', str(tmp))
        finally:
            tmp.unlink(missing_ok=True)

        # loaddata writes raw model values and therefore does not generate SEO URLs.
        for item in ShowcaseItem.objects.filter(seo_slug__isnull=True):
            item.save()

        if settings_objs:
            fields = dict(settings_objs[0].get('fields') or {})
            fields.pop('updated_at', None)
            # токен в дампе пустой — не затираем уже настроенный на сервере
            s = SiteSettings.load()
            for key, val in fields.items():
                if key in ('telegram_bot_token', 'telegram_chat_id') and not val:
                    continue
                setattr(s, key, val)
            s.save()
            self.stdout.write('SiteSettings updated from fixture')

        cache.delete('public_showcase')
        cache.delete('public_site_settings')
        self.stdout.write(self.style.SUCCESS(
            f'Loaded {len(content_only)} content objects from {path}'
        ))
