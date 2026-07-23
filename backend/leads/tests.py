import json
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase, override_settings

from leads.models import Lead


class LeadApiTests(TestCase):
    def setUp(self):
        cache.clear()

    @patch('leads.views.notify_telegram', return_value={'ok': True})
    @patch('leads.views.lookup_geo', return_value={'country': '', 'city': ''})
    def test_creates_lead(self, _geo, _telegram):
        response = self.client.post(
            '/api/leads/',
            data=json.dumps({'name': 'Иван', 'contact': '@ivan', 'message': 'CRM'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Lead.objects.count(), 1)

    def test_honeypot_silently_discards_bot(self):
        response = self.client.post(
            '/api/leads/',
            data=json.dumps({'name': 'Bot', 'contact': 'x', 'company_website': 'spam.test'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Lead.objects.count(), 0)

    @override_settings(LEAD_RATE_LIMIT=1)
    def test_rate_limit(self):
        payload = json.dumps({'name': 'Bot', 'contact': 'x', 'company_website': 'spam.test'})
        self.client.post('/api/leads/', data=payload, content_type='application/json')
        response = self.client.post('/api/leads/', data=payload, content_type='application/json')
        self.assertEqual(response.status_code, 429)
