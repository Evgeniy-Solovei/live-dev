import re

from django.core.cache import cache
from django.test import TestCase, override_settings

from content.models import ShowcaseCategory, ShowcaseItem
from content.seo import SERVICES, SERVICE_ORDER


@override_settings(SECURE_SSL_REDIRECT=False)
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


@override_settings(SECURE_SSL_REDIRECT=False)
class SeoPageTests(TestCase):
    def setUp(self):
        self.items_by_category = {}
        category_slugs = {data['category_slugs'][0] for data in SERVICES.values()}
        for position, category_slug in enumerate(sorted(category_slugs), start=1):
            category = ShowcaseCategory.objects.create(
                slug=category_slug,
                label=f'Категория {category_slug}',
                sort_order=position,
            )
            self.items_by_category[category_slug] = ShowcaseItem.objects.create(
                category=category,
                title=f'Проект {category_slug}',
                text=f'Описание проекта категории {category_slug}.',
                points=['интеграции', 'автоматизация', 'аналитика'],
                image_url=f'assets/showcase/{category_slug}-1.webp',
            )
        self.item = self.items_by_category['crm']

    def test_all_service_pages_are_indexable(self):
        self.assertEqual(self.client.get('/uslugi/').status_code, 301)
        for slug in SERVICE_ORDER:
            response = self.client.get(f'/uslugi/{slug}/')
            self.assertEqual(response.status_code, 200, slug)
            self.assertContains(response, '<main id="top">', html=False)
            self.assertContains(response, 'Витебск')
            self.assertContains(response, 'application/ld+json')
            self.assertContains(response, 'window.LIVEDEV_INITIAL_CATEGORY=', html=False)
            self.assertNotContains(response, '<meta name="robots" content="noindex', html=False)
            self.assertNotIn('X-Robots-Tag', response.headers)

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
                f'<meta property="og:url" content="{canonical}" />',
                html=False,
            )
            self.assertContains(
                response,
                f'window.LIVEDEV_INITIAL_CATEGORY="{expected["category_slugs"][0]}";',
                html=False,
            )
            self.assertContains(
                response,
                f'<h2 id="serviceProjectsHeading">{expected["project_heading"]}</h2>',
                html=False,
            )
            self.assertContains(
                response,
                f'<p id="serviceProjectsIntro">{expected["project_intro"]}</p>',
                html=False,
            )
            self.assertContains(
                response,
                f'data-product-category="{expected["category_slugs"][0]}"',
                html=False,
            )
            self.assertRegex(
                response.content.decode(),
                rf'class="product-tab is-active"[^>]*data-product-category="{re.escape(expected["category_slugs"][0])}"',
            )
            self.assertContains(
                response,
                f'<h3 id="showcaseTitle">Проект {expected["category_slugs"][0]}</h3>',
                html=False,
            )

            title_match = re.search(r'<title>(.*?)</title>', response.content.decode())
            self.assertIsNotNone(title_match)
            self.assertNotIn('Витебск', title_match.group(1))

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
        self.assertNotContains(response, '/privacy/')

    def test_home_has_indexable_metadata_and_structured_data(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '<title>Разработка сайтов, CRM и Telegram-сервисов в Беларуси — LiveDev</title>',
            html=False,
        )
        self.assertContains(response, '"@type": "ProfessionalService"', html=False)
        self.assertContains(response, '"@type": "FAQPage"', html=False)
        self.assertContains(response, 'https://live-dev.by/assets/livedev-logo.svg', html=False)
        self.assertNotContains(response, '<meta name="robots" content="noindex', html=False)
        self.assertNotIn('X-Robots-Tag', response.headers)

    def test_robots_allows_public_pages_and_points_to_sitemap(self):
        response = self.client.get('/robots.txt')
        self.assertEqual(response.status_code, 200)
        body = b''.join(response.streaming_content).decode()
        self.assertIn('User-agent: *', body)
        self.assertIn('Allow: /', body)
        self.assertIn('Sitemap: https://live-dev.by/sitemap.xml', body)
