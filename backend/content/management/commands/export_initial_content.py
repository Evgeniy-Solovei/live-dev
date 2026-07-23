"""Обновить fixtures/initial_content.json из текущей БД (перед деплоем)."""
from pathlib import Path

from django.core.management import BaseCommand, call_command


class Command(BaseCommand):
    help = 'Экспорт витрины + SiteSettings в fixtures/initial_content.json (без токена Telegram)'

    def handle(self, *args, **options):
        out = Path(__file__).resolve().parents[3] / 'fixtures' / 'initial_content.json'
        out.parent.mkdir(parents=True, exist_ok=True)
        call_command(
            'dumpdata',
            'content',
            'core.SiteSettings',
            indent=2,
            output=str(out),
        )

        import json

        data = json.loads(out.read_text(encoding='utf-8'))
        for obj in data:
            if obj.get('model') == 'core.sitesettings':
                fields = obj.setdefault('fields', {})
                fields['telegram_bot_token'] = ''
                fields['telegram_chat_id'] = ''
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        self.stdout.write(self.style.SUCCESS(f'Saved {out} ({len(data)} objects)'))
