import json
from unittest.mock import patch

from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings

from core.models import SiteSettings
from leads.models import Lead


class LeadApiTests(TestCase):
    def setUp(self):
        cache.clear()

    @patch('leads.views.notify_telegram', return_value={'ok': True})
    @patch('leads.views.notify_email', return_value={'ok': True})
    @patch('leads.views.lookup_geo', return_value={'country': '', 'city': ''})
    def test_creates_lead(self, _geo, email, _telegram):
        response = self.client.post(
            '/api/leads/',
            data=json.dumps({'name': 'Иван', 'contact': '@ivan', 'message': 'CRM'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Lead.objects.count(), 1)
        self.assertTrue(response.json()['email'])
        email.assert_called_once()

    def test_honeypot_silently_discards_bot(self):
        response = self.client.post(
            '/api/leads/',
            data=json.dumps({'name': 'Bot', 'contact': 'x', 'company_website': 'spam.test'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Lead.objects.count(), 0)

    @override_settings(
        EMAIL_NOTIFICATIONS_ENABLED=True,
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        EMAIL_HOST_USER='sender@example.com',
        EMAIL_HOST_PASSWORD='test-password',
        DEFAULT_FROM_EMAIL='sender@example.com',
    )
    @patch('leads.views.notify_telegram', return_value={'ok': True})
    @patch('leads.views.lookup_geo', return_value={'country': 'Беларусь', 'city': 'Витебск'})
    def test_sends_lead_to_contact_email(self, _geo, _telegram):
        settings_obj = SiteSettings.load()
        settings_obj.contact_email = 'orders@example.com'
        settings_obj.save()
        response = self.client.post(
            '/api/leads/',
            data=json.dumps({
                'name': 'Анна',
                'contact': 'anna@example.com',
                'message': 'Нужен лендинг',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['email'])
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['orders@example.com'])
        self.assertEqual(mail.outbox[0].reply_to, ['anna@example.com'])
        self.assertIn('Нужен лендинг', mail.outbox[0].body)

    @override_settings(LEAD_RATE_LIMIT=1)
    def test_rate_limit(self):
        payload = json.dumps({'name': 'Bot', 'contact': 'x', 'company_website': 'spam.test'})
        self.client.post('/api/leads/', data=payload, content_type='application/json')
        response = self.client.post('/api/leads/', data=payload, content_type='application/json')
        self.assertEqual(response.status_code, 429)
