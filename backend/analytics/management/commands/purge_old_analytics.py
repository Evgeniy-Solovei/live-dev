from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from analytics.models import PageVisit


class Command(BaseCommand):
    help = 'Delete analytics visits and related events older than the retention period'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=365)

    def handle(self, *args, **options):
        days = max(30, options['days'])
        cutoff = timezone.now() - timedelta(days=days)
        count, _ = PageVisit.objects.filter(started_at__lt=cutoff).delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {count} old analytics records'))
