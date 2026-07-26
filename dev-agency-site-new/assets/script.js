const revealItems = document.querySelectorAll('.reveal');
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (!entry.isIntersecting) return;
    entry.target.classList.add('is-visible');
    revealObserver.unobserve(entry.target);
  });
}, {
  threshold: 0.1,
  rootMargin: '0px 0px -6% 0px',
});

const revealInView = () => {
  const vh = window.innerHeight;
  revealItems.forEach((el) => {
    if (el.classList.contains('is-visible')) return;
    const rect = el.getBoundingClientRect();
    if (rect.top < vh - 8 && rect.bottom > 0) {
      el.classList.add('is-visible');
      revealObserver.unobserve(el);
    }
  });
};

revealItems.forEach((el, index) => {
  if (prefersReducedMotion) {
    el.classList.add('is-visible');
    return;
  }
  el.style.transitionDelay = `${Math.min((index % 4) * 40, 120)}ms`;
  revealObserver.observe(el);
});

revealInView();

if (!prefersReducedMotion) {
  let scrollTick = false;
  window.addEventListener('scroll', () => {
    if (scrollTick) return;
    scrollTick = true;
    requestAnimationFrame(() => {
      scrollTick = false;
      revealInView();
    });
  }, { passive: true });
}

const glow = document.getElementById('cursorGlow');
let glowX = 0;
let glowY = 0;
let glowFrame = null;
const moveGlow = () => {
  glowFrame = null;
  if (!glow) return;
  glow.style.left = `${glowX}px`;
  glow.style.top = `${glowY}px`;
};
window.addEventListener('pointermove', (event) => {
  if (!glow || window.matchMedia('(pointer: coarse)').matches) return;
  glowX = event.clientX;
  glowY = event.clientY;
  if (!glowFrame) glowFrame = requestAnimationFrame(moveGlow);
}, { passive: true });

const burger = document.getElementById('burger');
const header = document.querySelector('.site-header');
const setMenuOpen = (isOpen) => {
  if (!header || !burger) return;
  header.classList.toggle('is-open', isOpen);
  burger.setAttribute('aria-expanded', String(isOpen));
};
burger?.addEventListener('click', (event) => {
  event.stopPropagation();
  setMenuOpen(!header?.classList.contains('is-open'));
});
document.querySelectorAll('.nav a').forEach((link) => {
  link.addEventListener('click', () => setMenuOpen(false));
});
document.addEventListener('click', (event) => {
  if (!header?.classList.contains('is-open')) return;
  if (header.contains(event.target)) return;
  setMenuOpen(false);
});
document.addEventListener('keydown', (event) => {
  if (event.key !== 'Escape') return;
  setMenuOpen(false);
  burger?.focus();
});

const progress = document.getElementById('scrollProgress');
const updateProgress = () => {
  if (!progress) return;
  const scrollable = document.documentElement.scrollHeight - window.innerHeight;
  const percent = scrollable > 0 ? (window.scrollY / scrollable) * 100 : 0;
  progress.style.width = `${Math.min(100, Math.max(0, percent))}%`;
};
window.addEventListener('scroll', updateProgress, { passive: true });
window.addEventListener('resize', updateProgress);
updateProgress();

/** Fallback if backend /api/showcase/ unavailable. Prefer CMS data via livedev:showcase. */
const productExamplesFallback = {
  crm: {
    label: 'CRM и личные кабинеты',
    items: [
      {
        title: 'Учёт баллонов',
        text: 'Склад, заправка и аттестация в одном кабинете.',
        points: ['склад','заправка','аттестация'],
        image: 'assets/showcase/crm-1.webp'
      },
      {
        title: 'CRM круизов',
        text: 'Брони, оплаты и аналитика в одном потоке.',
        points: ['брони','оплаты','аналитика'],
        image: 'assets/showcase/crm-2.webp'
      },
      {
        title: '«Честный знак»',
        text: 'Товары, остатки и отчёты без ручной рутины.',
        points: ['товары','остатки','отчёты'],
        image: 'assets/showcase/crm-3.webp'
      },
      {
        title: 'Личный кабинет',
        text: 'Баланс, платежи и документы в одном месте.',
        points: ['баланс','платежи','документы'],
        image: 'assets/showcase/crm-4.webp'
      },
      {
        title: 'CRM салона',
        text: 'Онлайн-запись, календарь и напоминания.',
        points: ['запись','календарь','напоминания'],
        image: 'assets/showcase/crm-5.webp'
      }
    ]
  },
  telegram: {
    label: 'Telegram Mini App',
    items: [
      { title: 'Запись на услуги', text: 'Каталог, онлайн-запись и статусы заказа.', points: ['каталог','запись','статусы'], image: 'assets/showcase/tg-booking.webp' },
      { title: 'Skillbox «Бокси»', text: 'Тап-игра, награды и задания в Telegram.', points: ['тап-игра','награды','задания'], image: 'assets/showcase/tg-1.webp' },
      { title: 'Irwin', text: 'Питомцы, коллекция и бонусы в Mini App.', points: ['питомцы','бонусы','задания'], image: 'assets/showcase/tg-2.webp' },
      { title: 'Royal Tap', text: 'Аркада с прокачкой героев и PvP.', points: ['аркада','прокачка','PvP'], image: 'assets/showcase/tg-3.webp' },
      { title: 'Енот (Fortune)', text: 'Прокачка, скины и задания с наградами.', points: ['прокачка','скины','бонусы'], image: 'assets/showcase/tg-4.webp' },
      { title: 'RNDVU', text: 'Лента, лайки и чаты для знакомств.', points: ['лента','лайки','чаты'], image: 'assets/showcase/tg-5.webp' },
      { title: 'АстроКухня', text: 'Рецепты по астрокарте и учёт КЖБУ.', points: ['рецепты','астрология','КЖБУ'], image: 'assets/showcase/tg-6.webp' }
    ]
  },
  bots: {
    label: 'Боты для мессенджеров',
    items: [
      { title: 'Бот автосервиса', text: 'Онлайн-запись, цены от админа, учёт расходов и уведомления клиенту.', points: ['запись','цены','расходы'], image: 'assets/showcase/bots-1.webp' },
      { title: 'Бот подарков', text: 'Участник дарит подарок — он распределяется по рефералам. Заработок и радость для всех.', points: ['подарки','рефералы','доход'], image: 'assets/showcase/bots-2.webp' },
      { title: 'Бот английского', text: 'Ежедневные задания, аудио-практика речи и путь с нуля до уровня C2.', points: ['задания','аудио','A0–C2'], image: 'assets/showcase/bots-3.webp' },
      { title: 'Бот поддержки', text: 'Ответы из базы знаний и помощь клиентам. Telegram, VK и MAX — автоматизация поддержки.', points: ['база знаний','Telegram','VK · MAX'], image: 'assets/showcase/bots-4.webp' },
      { title: 'Финансовый бот', text: 'Учёт трат, анализ расходов, цели на покупки и копилка — финансовая грамотность в Telegram.', points: ['траты','анализ','копилка'], image: 'assets/showcase/bots-5.webp' }
    ]
  },
  landings: {
    label: 'Лендинги',
    items: [
      { title: 'Turtle Cruise', text: 'Круизы на Кипре: маршруты, флот и онлайн-бронирование.', points: ['круизы','флот','бронь'], image: 'assets/showcase/land-1.webp' },
      { title: 'Ремонт под ключ', text: 'Ремонт квартир и домов в Минске: смета, портфолио и заявка.', points: ['ремонт','смета','заявка'], image: 'assets/showcase/land-2.webp' },
      { title: 'Автосервис', text: 'Диагностика и ремонт авто: услуги, цены и онлайн-запись.', points: ['диагностика','ремонт','запись'], image: 'assets/showcase/land-3.webp' },
      { title: 'Quest House', text: 'Хоррор-квесты: уровни страха, расписание и онлайн-бронь.', points: ['квесты','бронь','атмосфера'], image: 'assets/showcase/land-4.webp' },
      { title: 'Психолог', text: 'Консультации онлайн и офлайн: услуги, цены и запись на сессию.', points: ['консультации','запись','онлайн'], image: 'assets/showcase/land-5.webp' }
    ]
  },
  shop: {
    label: 'Сайты и приложения',
    items: [
      { title: 'Solovey Desert', text: 'Авторские торты и десерты: каталог, корзина и заказ онлайн.', points: ['каталог','корзина','заказ'], image: 'assets/showcase/shop-1.webp' },
      { title: 'NEXORA', text: 'Магазин гаджетов: каталог смартфонов, фильтры и оформление заказа.', points: ['каталог','фильтры','заказ'], image: 'assets/showcase/shop-2.webp' },
      { title: 'WooDecor', text: 'Магазин деревянных сувениров: каталог, корзина и индивидуальный заказ.', points: ['каталог','ручная работа','заказ'], image: 'assets/showcase/shop-3.webp' }
    ]
  },
  ai: {
    label: 'AI-автоматизация',
    items: [
      { title: 'AI-агент для бизнеса', text: 'Диалоги, заявки и продажи на автопилоте. Каналы, автоматизации и тарифы от 99 BYN.', points: ['диалоги','заявки','автоматизация'], image: 'assets/showcase/ai-1.webp' },
      { title: 'AI-продажи', text: 'Воронка на автопилоте: поиск лидов, квалификация, прогрев и сделки с AI-агентами.', points: ['лиды','воронка','агенты'], image: 'assets/showcase/ai-2.webp' },
      { title: 'Разбор документов', text: 'Счета, акты и накладные в CRM: распознавание, проверка данных и заполнение полей.', points: ['распознавание','CRM','экономия'], image: 'assets/showcase/ai-3.webp' }
    ]
  },
  vpn: {
    label: 'VPN и инфраструктура',
    items: [
      { title: 'VPN-сервис', text: 'Шифрование, серверы и мониторинг сети. Старт 12 BYN / мес, Про 29 BYN. Поддержка 24/7 на +375 29 200-30-40.', points: ['шифрование','серверы','мониторинг'], image: 'assets/showcase/vpn-1.webp' },
      { title: 'Закрытая сеть для команды', text: 'Доступы сотрудников к CRM и админкам. Админ сети: +375 33 450-60-70.', points: ['сотрудники','роли','контроль'], image: 'assets/showcase/vpn-2.webp' },
      { title: 'Инфраструктура запуска', text: 'Серверы, SSL, бэкапы и алерты в Telegram на +375 — продукт живёт стабильно после релиза.', points: ['серверы','бэкапы','алерты'], image: 'assets/showcase/vpn-3.webp' }
    ]
  }
};

let productExamples = window.LIVEDEV_SHOWCASE || productExamplesFallback;

document.addEventListener('livedev:showcase', (event) => {
  if (!event.detail || !Object.keys(event.detail).length) return;
  productExamples = event.detail;
  syncProductTabs();
  if (!productExamples[activeCategory]) {
    activeCategory = Object.keys(productExamples)[0] || 'crm';
  }
  activeExample = 0;
  renderShowcase(true);
});

const productTabsRoot = document.querySelector('.product-tabs');
let productTabs = document.querySelectorAll('[data-product-category]');
const showcase = document.getElementById('productShowcase');
const showcaseVisual = document.getElementById('showcaseVisual');
const showcaseCategory = document.getElementById('showcaseCategory');
const showcaseTitle = document.getElementById('showcaseTitle');
const showcaseText = document.getElementById('showcaseText');
const showcasePoints = document.getElementById('showcasePoints');
const showcaseCounter = document.getElementById('showcaseCounter');
const showcaseContent = showcase?.querySelector('.showcase-content');
const serviceProjectsHeading = document.getElementById('serviceProjectsHeading');
const serviceProjectsIntro = document.getElementById('serviceProjectsIntro');
let activeCategory = window.LIVEDEV_INITIAL_CATEGORY || 'crm';
let activeExample = 0;
let showcaseTimer = null;

const bindProductTabs = () => {
  productTabs = document.querySelectorAll('[data-product-category]');
  productTabs.forEach((tab) => {
    tab.onclick = (event) => {
      event.preventDefault();
      activeCategory = tab.dataset.productCategory;
      activeExample = 0;
      productTabs.forEach((item) => item.classList.toggle('is-active', item === tab));
      if (window.location.pathname !== tab.getAttribute('href')) {
        window.history.pushState({ productCategory: activeCategory }, '', tab.href);
      }
      renderShowcase();
    };
  });
};

const categoryServiceUrls = {
  crm: '/uslugi/crm-sistemy/',
  telegram: '/uslugi/telegram-mini-app/',
  bots: '/uslugi/telegram-boty/',
  landings: '/uslugi/landing-page/',
  shop: '/uslugi/razrabotka-saitov/',
  ai: '/uslugi/ai-avtomatizaciya/',
  vpn: '/uslugi/podderzhka-proektov/',
};

const categoryByServicePath = Object.fromEntries(
  Object.entries(categoryServiceUrls).map(([category, path]) => [path, category]),
);

const categoryServiceCopy = {
  crm: {
    heading: 'Разработка CRM-систем для бизнеса',
    intro: 'Разрабатываем CRM-системы, личные кабинеты и внутренние сервисы под процессы компании. Автоматизируем заявки, задачи, документы, оплаты и отчётность.',
  },
  telegram: {
    heading: 'Разработка Telegram Mini Apps под ключ',
    intro: 'Разрабатываем Telegram Mini Apps для каталогов, личных кабинетов, программ лояльности, оплат и автоматизации бизнеса. Подключаем API, CRM и платёжные системы.',
  },
  bots: {
    heading: 'Разработка Telegram-ботов для бизнеса',
    intro: 'Создаём ботов для приёма заявок, записи, поддержки, продаж и уведомлений. Интегрируем их с CRM, сайтом, базой данных и внешними сервисами.',
  },
  landings: {
    heading: 'Разработка лендингов под ключ',
    intro: 'Создаём посадочные страницы под услуги, продукты и рекламные кампании. Продумываем структуру, адаптив, формы заявок, аналитику и техническое SEO.',
  },
  shop: {
    heading: 'Разработка сайтов и веб-сервисов под ключ',
    intro: 'Создаём лендинги, корпоративные сайты, личные кабинеты и веб-сервисы для бизнеса. Подключаем CRM, оплату, аналитику и внешние API.',
  },
  ai: {
    heading: 'AI-автоматизация и AI-агенты',
    intro: 'Внедряем AI-агентов, поиск по базе знаний и автоматическую обработку обращений и документов. Интегрируем решения с CRM, мессенджерами и рабочими процессами.',
  },
  vpn: {
    heading: 'Поддержка проектов, VPN и инфраструктуры',
    intro: 'Поддерживаем сайты, CRM, backend и серверную инфраструктуру после запуска. Настраиваем мониторинг, резервные копии, VPN и безопасное развёртывание.',
  },
};

const renderServiceCopy = () => {
  const pathCopy = window.LIVEDEV_SERVICE_COPY_BY_PATH?.[window.location.pathname];
  const copy = pathCopy || categoryServiceCopy[activeCategory];
  if (!copy) return;
  if (serviceProjectsHeading) serviceProjectsHeading.textContent = copy.heading;
  if (serviceProjectsIntro) serviceProjectsIntro.textContent = copy.intro;
};

/** Rebuild category links from CMS data (order = API order). */
const syncProductTabs = () => {
  if (!productTabsRoot) return;
  const keys = Object.keys(productExamples);
  if (!keys.length) return;
  const buttons = keys.map((slug, i) => {
    const label = productExamples[slug].label || slug;
    const active = slug === activeCategory || (!productExamples[activeCategory] && i === 0);
    const link = document.createElement('a');
    link.className = `product-tab${active ? ' is-active' : ''}`;
    link.href = categoryServiceUrls[slug] || '/uslugi/';
    link.dataset.productCategory = slug;
    link.textContent = label;
    return link;
  });
  productTabsRoot.replaceChildren(...buttons);
  bindProductTabs();
};

const visualNode = (category, item) => {
  let src = item?.image || category?.image;
  if (src?.startsWith('assets/')) src = `/${src}`;
  if (src) {
    const bust = src.includes('?') ? src : `${src}?v=20260723u`;
    const img = document.createElement('img');
    img.className = 'showcase-shot';
    img.src = bust;
    img.alt = item?.title || category?.label || 'Пример работы';
    img.width = 1600;
    img.height = 900;
    img.decoding = 'async';
    img.fetchPriority = 'high';
    return img;
  }
  const placeholder = document.createElement('div');
  placeholder.className = 'wide-preview crm-preview-big';
  return placeholder;
};

const renderShowcase = (instant = false) => {
  const category = productExamples[activeCategory];
  const item = category.items[activeExample];
  const apply = () => {
    renderServiceCopy();
    if (showcaseVisual) showcaseVisual.replaceChildren(visualNode(category, item));
    if (showcaseCategory) showcaseCategory.textContent = category.label;
    if (showcaseTitle) showcaseTitle.textContent = item.title;
    if (showcaseText) showcaseText.textContent = item.text;
    // Ровно 3 тега — иначе сетка/высота прыгает
    const points = (item.points || []).slice(0, 3);
    if (showcasePoints) {
      showcasePoints.replaceChildren(...points.map((point) => {
        const tag = document.createElement('span');
        tag.textContent = point;
        return tag;
      }));
    }
    if (showcaseCounter) showcaseCounter.textContent = `${activeExample + 1} / ${category.items.length}`;
    showcase?.classList.remove('is-changing');
    showcaseTimer = null;
    // Только действия пользователя (стрелки / вкладки), не первый рендер и не подгрузка API
    if (!instant) {
      try {
        window.LiveDevAPI?.track?.('showcase', {
          payload: {
            category: activeCategory,
            category_label: category.label,
            title: item.title,
            index: activeExample,
          },
        });
      } catch (e) { /* ignore */ }
    }
  };

  if (instant) {
    if (showcaseTimer) clearTimeout(showcaseTimer);
    apply();
    return;
  }

  if (showcaseTimer) clearTimeout(showcaseTimer);
  showcase?.classList.add('is-changing');
  showcaseTimer = setTimeout(apply, 140);
};

const getShowcaseLayoutMode = () => {
  if (window.innerWidth <= 640) return 'mobile';
  if (window.innerWidth <= 980) return 'tablet';
  return 'desktop';
};

let showcaseLayoutMode = getShowcaseLayoutMode();

productTabs.forEach((item) => {
  item.classList.toggle('is-active', item.dataset.productCategory === activeCategory);
});
renderShowcase(true);

/* Фиксированная высота через CSS — без прогона всех слайдов */
const fixedShowcaseHeights = {
  desktop: { blockHeight: 560 },
  tablet: { contentHeight: 360 },
  mobile: { contentHeight: 340 },
};

const applyShowcaseHeights = (metrics, mode) => {
  if (!showcase) return;
  document.documentElement.style.removeProperty('--showcase-block-height');
  document.documentElement.style.removeProperty('--showcase-visual-height');
  document.documentElement.style.removeProperty('--showcase-content-height');
  showcase.classList.add('is-height-locked');

  if (mode === 'desktop') {
    document.documentElement.style.setProperty('--showcase-block-height', `${metrics.blockHeight}px`);
    return;
  }

  if (metrics.contentHeight) {
    document.documentElement.style.setProperty('--showcase-content-height', `${metrics.contentHeight}px`);
  }
};

const lockShowcaseHeight = () => {
  const mode = getShowcaseLayoutMode();
  applyShowcaseHeights(fixedShowcaseHeights[mode], mode);
};

bindProductTabs();
window.addEventListener('popstate', () => {
  const category = categoryByServicePath[window.location.pathname] || 'crm';
  if (!productExamples[category]) return;
  activeCategory = category;
  activeExample = 0;
  productTabs.forEach((item) => item.classList.toggle('is-active', item.dataset.productCategory === category));
  renderShowcase(true);
});
document.querySelector('[data-example-prev]')?.addEventListener('click', () => {
  const list = productExamples[activeCategory].items;
  activeExample = (activeExample - 1 + list.length) % list.length;
  renderShowcase();
});
document.querySelector('[data-example-next]')?.addEventListener('click', () => {
  const list = productExamples[activeCategory].items;
  activeExample = (activeExample + 1) % list.length;
  renderShowcase();
});

lockShowcaseHeight();
window.addEventListener('resize', () => {
  const mode = getShowcaseLayoutMode();
  if (mode === showcaseLayoutMode) return;
  showcaseLayoutMode = mode;
  lockShowcaseHeight();
});

const leadForm = document.getElementById('leadForm');
const leadFormFeedback = document.getElementById('leadFormFeedback');
const leadSuccess = document.getElementById('leadSuccess');
const leadSuccessAction = leadSuccess?.querySelector('.lead-success-action');
let leadSuccessPreviousFocus = null;

const setLeadFeedback = (message = '', type = '') => {
  if (!leadFormFeedback) return;
  leadFormFeedback.textContent = message;
  leadFormFeedback.classList.toggle('is-error', type === 'error');
};

const openLeadSuccess = () => {
  if (!leadSuccess) return;
  leadSuccessPreviousFocus = document.activeElement;
  leadSuccess.hidden = false;
  document.body.classList.add('lead-success-open');
  requestAnimationFrame(() => {
    leadSuccess.classList.add('is-visible');
    leadSuccessAction?.focus();
  });
};

const closeLeadSuccess = () => {
  if (!leadSuccess || leadSuccess.hidden) return;
  leadSuccess.classList.remove('is-visible');
  document.body.classList.remove('lead-success-open');
  window.setTimeout(() => {
    leadSuccess.hidden = true;
    leadSuccessPreviousFocus?.focus?.();
  }, 220);
};

leadSuccess?.querySelectorAll('[data-lead-success-close]').forEach((control) => {
  control.addEventListener('click', closeLeadSuccess);
});
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && !leadSuccess?.hidden) closeLeadSuccess();
});

leadForm?.addEventListener('submit', async (event) => {
  event.preventDefault();
  setLeadFeedback();
  const fd = new FormData(leadForm);
  const payload = {
    name: String(fd.get('name') || '').trim(),
    contact: String(fd.get('contact') || '').trim(),
    message: String(fd.get('message') || '').trim(),
    company_website: String(fd.get('company_website') || '').trim(),
    page_url: location.href,
    source: 'site_form',
  };
  const btn = leadForm.querySelector('button[type="submit"]');
  const prev = btn?.textContent;
  if (btn) { btn.disabled = true; btn.textContent = 'Отправка…'; }
  try {
    if (!window.LiveDevAPI?.postLead) throw new Error('no api');
    await window.LiveDevAPI.postLead(payload);
    window.LiveDevAPI.reachGoal?.(window.LIVEDEV_SETTINGS?.lead_goal_name || 'lead_submit');
    window.LiveDevAPI.reportLeadConversion?.();
    leadForm.reset();
    openLeadSuccess();
  } catch (e) {
    setLeadFeedback('Не удалось отправить заявку. Напишите в Telegram @solovey_ev или на live-dev@mail.ru.', 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = prev || 'Получить оценку проекта'; }
  }
});

const copyToast = document.getElementById('copyToast');
const showCopyToast = (message = 'Скопировано') => {
  if (!copyToast) return;
  copyToast.textContent = message;
  copyToast.classList.add('is-visible');
  clearTimeout(window.__copyToastTimer);
  window.__copyToastTimer = setTimeout(() => copyToast.classList.remove('is-visible'), 1400);
};
const fallbackCopy = (value) => {
  const textarea = document.createElement('textarea');
  textarea.value = value;
  textarea.setAttribute('readonly', 'readonly');
  textarea.style.position = 'fixed';
  textarea.style.left = '-9999px';
  textarea.style.top = '0';
  document.body.appendChild(textarea);
  textarea.focus();
  textarea.select();
  textarea.setSelectionRange(0, textarea.value.length);
  let ok = false;
  try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
  document.body.removeChild(textarea);
  return ok;
};
const copyValue = async (value) => {
  let copied = fallbackCopy(value);
  if (!copied && navigator.clipboard?.writeText) {
    try { await navigator.clipboard.writeText(value); copied = true; } catch (e) {}
  }
  showCopyToast(copied ? 'Скопировано' : 'Не скопировалось');
};
document.addEventListener('click', (event) => {
  const target = event.target.closest('[data-copy-value]');
  if (!target) return;
  event.preventDefault();
  copyValue(target.getAttribute('data-copy-value'));
});
