from django.core.management.base import BaseCommand

from content.models import ShowcaseCategory, ShowcaseItem
from core.models import SiteSettings


SEED = [
    ('crm', 'CRM и личные кабинеты', [
        ('Учёт баллонов',
         'Склад, заправка и аттестация в одном кабинете.',
         ['склад', 'заправка', 'аттестация'],
         'assets/showcase/crm-1.webp'),
        ('CRM круизов',
         'Брони, оплаты и аналитика в одном потоке.',
         ['брони', 'оплаты', 'аналитика'],
         'assets/showcase/crm-2.webp'),
        ('«Честный знак»',
         'Товары, остатки и отчёты без ручной рутины.',
         ['товары', 'остатки', 'отчёты'],
         'assets/showcase/crm-3.webp'),
        ('Личный кабинет',
         'Баланс, платежи и документы в одном месте.',
         ['баланс', 'платежи', 'документы'],
         'assets/showcase/crm-4.webp'),
        ('CRM салона',
         'Онлайн-запись, календарь и напоминания.',
         ['запись', 'календарь', 'напоминания'],
         'assets/showcase/crm-5.webp'),
    ]),
    ('telegram', 'Telegram Mini App', [
        ('Запись на услуги',
         'Каталог, онлайн-запись и статусы заказа.',
         ['каталог', 'запись', 'статусы'],
         'assets/showcase/tg-booking.webp'),
        ('Skillbox «Бокси»',
         'Тап-игра, награды и задания в Telegram.',
         ['тап-игра', 'награды', 'задания'],
         'assets/showcase/tg-1.webp'),
        ('Irwin',
         'Питомцы, коллекция и бонусы в Mini App.',
         ['питомцы', 'бонусы', 'задания'],
         'assets/showcase/tg-2.webp'),
        ('Royal Tap',
         'Аркада с прокачкой героев и PvP.',
         ['аркада', 'прокачка', 'PvP'],
         'assets/showcase/tg-3.webp'),
        ('Енот (Fortune)',
         'Прокачка, скины и задания с наградами.',
         ['прокачка', 'скины', 'бонусы'],
         'assets/showcase/tg-4.webp'),
        ('RNDVU',
         'Лента, лайки и чаты для знакомств.',
         ['лента', 'лайки', 'чаты'],
         'assets/showcase/tg-5.webp'),
        ('АстроКухня',
         'Рецепты по астрокарте и учёт КЖБУ.',
         ['рецепты', 'астрология', 'КЖБУ'],
         'assets/showcase/tg-6.webp'),
    ]),
    ('bots', 'Боты для мессенджеров', [
        ('Бот автосервиса',
         'Онлайн-запись, цены от админа, учёт расходов и уведомления клиенту.',
         ['запись', 'цены', 'расходы'],
         'assets/showcase/bots-1.webp'),
        ('Бот подарков',
         'Участник дарит подарок — он распределяется по рефералам. Заработок и радость для всех.',
         ['подарки', 'рефералы', 'доход'],
         'assets/showcase/bots-2.webp'),
        ('Бот английского',
         'Ежедневные задания, аудио-практика речи и путь с нуля до уровня C2.',
         ['задания', 'аудио', 'A0–C2'],
         'assets/showcase/bots-3.webp'),
        ('Бот поддержки',
         'Ответы из базы знаний и помощь клиентам. Telegram, VK и MAX — автоматизация поддержки.',
         ['база знаний', 'Telegram', 'VK · MAX'],
         'assets/showcase/bots-4.webp'),
        ('Финансовый бот',
         'Учёт трат, анализ расходов, цели на покупки и копилка — финансовая грамотность в Telegram.',
         ['траты', 'анализ', 'копилка'],
         'assets/showcase/bots-5.webp'),
    ]),
    ('landings', 'Лендинги', [
        ('Turtle Cruise',
         'Круизы на Кипре: маршруты, флот и онлайн-бронирование.',
         ['круизы', 'флот', 'бронь'],
         'assets/showcase/land-1.webp'),
        ('Ремонт под ключ',
         'Ремонт квартир и домов в Минске: смета, портфолио и заявка.',
         ['ремонт', 'смета', 'заявка'],
         'assets/showcase/land-2.webp'),
        ('Автосервис',
         'Диагностика и ремонт авто: услуги, цены и онлайн-запись.',
         ['диагностика', 'ремонт', 'запись'],
         'assets/showcase/land-3.webp'),
        ('Quest House',
         'Хоррор-квесты: уровни страха, расписание и онлайн-бронь.',
         ['квесты', 'бронь', 'атмосфера'],
         'assets/showcase/land-4.webp'),
        ('Психолог',
         'Консультации онлайн и офлайн: услуги, цены и запись на сессию.',
         ['консультации', 'запись', 'онлайн'],
         'assets/showcase/land-5.webp'),
    ]),
    ('shop', 'Сайты и приложения', [
        ('Solovey Desert',
         'Авторские торты и десерты: каталог, корзина и заказ онлайн.',
         ['каталог', 'корзина', 'заказ'],
         'assets/showcase/shop-1.webp'),
        ('NEXORA',
         'Магазин гаджетов: каталог смартфонов, фильтры и оформление заказа.',
         ['каталог', 'фильтры', 'заказ'],
         'assets/showcase/shop-2.webp'),
        ('WooDecor',
         'Магазин деревянных сувениров: каталог, корзина и индивидуальный заказ.',
         ['каталог', 'ручная работа', 'заказ'],
         'assets/showcase/shop-3.webp'),
    ]),
    ('ai', 'AI-автоматизация', [
        ('AI-агент для бизнеса',
         'Диалоги, заявки и продажи на автопилоте. Каналы, автоматизации и тарифы от 99 BYN.',
         ['диалоги', 'заявки', 'автоматизация'],
         'assets/showcase/ai-1.webp'),
        ('AI-продажи',
         'Воронка на автопилоте: поиск лидов, квалификация, прогрев и сделки с AI-агентами.',
         ['лиды', 'воронка', 'агенты'],
         'assets/showcase/ai-2.webp'),
        ('Разбор документов',
         'Счета, акты и накладные в CRM: распознавание, проверка данных и заполнение полей.',
         ['распознавание', 'CRM', 'экономия'],
         'assets/showcase/ai-3.webp'),
    ]),
    ('vpn', 'VPN и инфраструктура', [
        ('VPN-сервис',
         'Шифрование, серверы и мониторинг сети. Старт 12 BYN / мес, Про 29 BYN. Поддержка 24/7 на +375 29 200-30-40.',
         ['шифрование', 'серверы', 'мониторинг'],
         'assets/showcase/vpn-1.webp'),
        ('Закрытая сеть для команды',
         'Доступы сотрудников к CRM и админкам. Админ сети: +375 33 450-60-70.',
         ['сотрудники', 'роли', 'контроль'],
         'assets/showcase/vpn-2.webp'),
        ('Инфраструктура запуска',
         'Серверы, SSL, бэкапы и алерты в Telegram на +375 — продукт живёт стабильно после релиза.',
         ['серверы', 'бэкапы', 'алерты'],
         'assets/showcase/vpn-3.webp'),
    ]),
]


class Command(BaseCommand):
    help = 'Seed showcase categories/items and site settings (синхрон с фронтовым fallback)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--replace',
            action='store_true',
            help='Удалить старые карточки раздела и записать seed заново',
        )

    def handle(self, *args, **options):
        from django.core.cache import cache

        SiteSettings.load()
        replace = options.get('replace', False)
        keep_slugs = set()
        for order, (slug, label, items) in enumerate(SEED):
            keep_slugs.add(slug)
            cat, _ = ShowcaseCategory.objects.update_or_create(
                slug=slug,
                defaults={'label': label, 'sort_order': order, 'is_active': True},
            )
            if replace:
                cat.items.all().delete()
            for i, (title, text, points, image_url) in enumerate(items):
                if replace:
                    ShowcaseItem.objects.create(
                        category=cat,
                        title=title,
                        text=text,
                        points=points,
                        image_url=image_url,
                        sort_order=i,
                        is_active=True,
                    )
                else:
                    # Prefer match by sort_order so title renames update in place
                    existing = cat.items.filter(sort_order=i).first()
                    if existing:
                        existing.title = title
                        existing.text = text
                        existing.points = points
                        existing.image_url = image_url
                        existing.is_active = True
                        existing.save()
                    else:
                        ShowcaseItem.objects.create(
                            category=cat,
                            title=title,
                            text=text,
                            points=points,
                            image_url=image_url,
                            sort_order=i,
                            is_active=True,
                        )
            # Убрать хвост старых карточек (старые лендинги и т.п.)
            cat.items.exclude(sort_order__in=range(len(items))).delete()

        ShowcaseCategory.objects.exclude(slug__in=keep_slugs).update(is_active=False)
        cache.delete('public_showcase')
        self.stdout.write(self.style.SUCCESS('Showcase + settings seeded'))
