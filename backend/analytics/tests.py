import json

from django.core.cache import cache
from django.test import TestCase

from analytics.models import PageVisit


class AnalyticsApiTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_rejects_invalid_session(self):
        response = self.client.post(
            '/api/analytics/beacon/',
            data=json.dumps({'event': 'view', 'session': 'short'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(PageVisit.objects.count(), 0)

    def test_invalid_duration_does_not_crash(self):
        response = self.client.post(
            '/api/analytics/beacon/',
            data=json.dumps({
                'event': 'view',
                'session': '12345678-1234-1234-1234-123456789012',
                'duration': 'not-a-number',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PageVisit.objects.get().duration_seconds, 0)
