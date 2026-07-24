from django.core.cache import cache
from django.test import TestCase

from content.models import ShowcaseCategory, ShowcaseItem
from content.seo import SERVICES, SERVICE_ORDER


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
        self.assertEqual(self.client.get('/uslugi/').status_code, 301)
        for slug in SERVICE_ORDER:
            response = self.client.get(f'/uslugi/{slug}/')
            self.assertEqual(response.status_code, 200, slug)
            self.assertContains(response, '<main id="top">', html=False)
            self.assertContains(response, 'Витебск')
            self.assertContains(response, 'application/ld+json')
            self.assertContains(response, 'window.LIVEDEV_INITIAL_CATEGORY=', html=False)

    def test_portfolio_pages_are_not_public(self):
        self.assertEqual(self.client.get(f'/portfolio/{self.item.seo_slug}/').status_code, 404)

    def test_all_service_pages_have_unique_metadata_and_initial_category(self):
        titles = set()
        descriptions = set()
        canonicals = set()

        for slug in SERVICE_ORDER:
            expected = SERVICES[slug]
            url = f'/uslugi/{slug}/'
            canonical = f'https://live-dev.by{url}'
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, f'<title>{expected["title"]}</title>', html=False)
            self.assertContains(
                response,
                f'<meta name="description" content="{expected["description"]}" />',
                html=False,
            )
            self.assertContains(
                response,
                f'<link rel="canonical" href="{canonical}" />',
                html=False,
            )
            self.assertContains(
                response,
                f'<meta property="og:title" content="{expected["title"]}" />',
                html=False,
            )
            self.assertContains(
                response,
                f'<meta property="og:description" content="{expected["description"]}" />',
                html=False,
            )
            self.assertContains(
                response,
                f'window.LIVEDEV_INITIAL_CATEGORY="{expected["category_slugs"][0]}";',
                html=False,
            )

            titles.add(expected['title'])
            descriptions.add(expected['description'])
            canonicals.add(canonical)

        self.assertEqual(len(titles), len(SERVICE_ORDER))
        self.assertEqual(len(descriptions), len(SERVICE_ORDER))
        self.assertEqual(len(canonicals), len(SERVICE_ORDER))

    def test_sitemap_contains_services_without_portfolio_pages(self):
        response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)
        for slug in SERVICE_ORDER:
            self.assertContains(response, f'/uslugi/{slug}/')
        self.assertNotContains(response, '/portfolio/')
