from django.core.cache import cache
from django.test import TestCase

from content.models import ShowcaseCategory, ShowcaseItem
from content.seo import SERVICE_ORDER


class ShowcaseApiTests(TestCase):
    def test_public_payload_and_cache_header(self):
        cache.clear()
        category = ShowcaseCategory.objects.create(slug='crm', label='CRM')
        ShowcaseItem.objects.create(
            category=category,
            title='Проект',
            text='Описание',
            points=['CRM'],
            image_url='assets/showcase/crm-1.webp',
        )
        response = self.client.get('/api/showcase/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('max-age=60', response['Cache-Control'])
        self.assertEqual(response.json()['crm']['items'][0]['title'], 'Проект')


class SeoPageTests(TestCase):
    def setUp(self):
        category = ShowcaseCategory.objects.create(slug='crm', label='CRM')
        self.item = ShowcaseItem.objects.create(
            category=category,
            title='CRM для отдела продаж',
            text='Система для управления заявками и клиентами.',
            points=['заявки', 'клиенты', 'аналитика'],
            image_url='assets/showcase/crm-1.webp',
        )

    def test_all_service_pages_are_indexable(self):
        self.assertEqual(self.client.get('/uslugi/').status_code, 200)
        for slug in SERVICE_ORDER:
            response = self.client.get(f'/uslugi/{slug}/')
            self.assertEqual(response.status_code, 200, slug)
            self.assertContains(response, '<meta name="robots" content="index,follow', html=False)
            self.assertContains(response, 'Витебск')
            self.assertContains(response, 'application/ld+json')

    def test_portfolio_page(self):
        response = self.client.get(f'/portfolio/{self.item.seo_slug}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.item.title)
        self.assertContains(response, self.item.text)
        self.assertContains(response, 'rel="canonical"')

    def test_sitemap_contains_services_and_portfolio(self):
        response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '/uslugi/razrabotka-saitov/')
        self.assertContains(response, f'/portfolio/{self.item.seo_slug}/')
