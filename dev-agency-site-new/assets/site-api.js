/**
 * LiveDev public API: settings (Yandex/GA), showcase, leads, analytics beacon.
 * Works behind nginx (/api) or local Django (http://127.0.0.1:8000/api).
 */
(function () {
  const API_BASE = window.LIVEDEV_API_BASE || '/api';

  const sessionKey = (() => {
    const k = 'ld_sid';
    let v = localStorage.getItem(k);
    if (!v) {
      v = (crypto.randomUUID && crypto.randomUUID()) || String(Date.now()) + Math.random().toString(16).slice(2);
      localStorage.setItem(k, v);
    }
    return v;
  })();

  let visitId = null;
  let startedAt = Date.now();
  let analyticsOn = true;

  const postJson = async (path, body) => {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      keepalive: true,
    });
    if (!res.ok) throw new Error('api ' + res.status);
    return res.json();
  };

  const getJson = async (path) => {
    const res = await fetch(`${API_BASE}${path}`, { credentials: 'same-origin' });
    if (!res.ok) throw new Error('api ' + res.status);
    return res.json();
  };

  const injectYandexMetrika = (id, webvisor) => {
    if (!id || window.ym) return;
    window.LIVEDEV_METRIKA_ID = id;
    (function (m, e, t, r, i) {
      m[i] = m[i] || function () { (m[i].a = m[i].a || []).push(arguments); };
      m[i].l = +new Date();
      const k = e.createElement(t);
      const a = e.getElementsByTagName(t)[0];
      k.async = 1;
      k.src = r;
      a.parentNode.insertBefore(k, a);
    })(window, document, 'script', 'https://mc.yandex.ru/metrika/tag.js', 'ym');
    window.ym(Number(id) || id, 'init', {
      clickmap: true,
      trackLinks: true,
      accurateTrackBounce: true,
      webvisor: !!webvisor,
    });
  };

  const reachGoal = (goalName, params) => {
    const id = window.LIVEDEV_METRIKA_ID;
    if (!id || typeof window.ym !== 'function' || !goalName) return;
    try {
      window.ym(Number(id) || id, 'reachGoal', goalName, params || undefined);
    } catch (e) { /* ignore */ }
  };

  const configuredGoogleIds = new Set();
  const injectGoogleTag = (measurementId) => {
    if (!measurementId || configuredGoogleIds.has(measurementId)) return;
    if (!window.__ldGoogleTagLoaded) {
      window.__ldGoogleTagLoaded = true;
      const s = document.createElement('script');
      s.async = true;
      s.src = `https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(measurementId)}`;
      document.head.appendChild(s);
    }
    window.dataLayer = window.dataLayer || [];
    if (!window.gtag) {
      window.gtag = function () { window.dataLayer.push(arguments); };
      window.gtag('js', new Date());
    }
    window.gtag('config', measurementId);
    configuredGoogleIds.add(measurementId);
  };

  const injectGTM = (gtmId) => {
    if (!gtmId || window.__ldGtm) return;
    window.__ldGtm = true;
    (function (w, d, s, l, i) {
      w[l] = w[l] || [];
      w[l].push({ 'gtm.start': new Date().getTime(), event: 'gtm.js' });
      const f = d.getElementsByTagName(s)[0];
      const j = d.createElement(s);
      const dl = l !== 'dataLayer' ? '&l=' + l : '';
      j.async = true;
      j.src = 'https://www.googletagmanager.com/gtm.js?id=' + i + dl;
      f.parentNode.insertBefore(j, f);
    })(window, document, 'script', 'dataLayer', gtmId);
  };

  const currentPath = () => {
    const hash = location.hash || '#top';
    return `${location.pathname}${hash}`;
  };

  const durationSec = () => Math.max(0, Math.round((Date.now() - startedAt) / 1000));

  const sendBeacon = async (event, extra = {}) => {
    if (!analyticsOn) return;
    try {
      const data = await postJson('/analytics/beacon/', {
        event,
        session: sessionKey,
        visit_id: visitId,
        path: currentPath(),
        title: document.title,
        referrer: document.referrer || '',
        duration: durationSec(),
        ...extra,
      });
      if (data.visit_id) visitId = data.visit_id;
    } catch (e) {
      /* ignore offline / no backend */
    }
  };

  const loadSettings = async () => {
    try {
      const s = await getJson('/settings/');
      analyticsOn = s.analytics_enabled !== false;
      if (s.yandex_metrika_id) injectYandexMetrika(s.yandex_metrika_id, s.yandex_metrika_webvisor);
      if (s.google_tag_manager_id) {
        injectGTM(s.google_tag_manager_id);
      } else {
        if (s.google_analytics_id) injectGoogleTag(s.google_analytics_id);
        if (s.google_ads_id) injectGoogleTag(s.google_ads_id);
      }
      window.LIVEDEV_SETTINGS = s;
      document.dispatchEvent(new CustomEvent('livedev:settings', { detail: s }));
    } catch (e) {
      window.LIVEDEV_SETTINGS = null;
    }
  };

  const loadShowcase = async () => {
    try {
      const data = await getJson('/showcase/');
      if (data && Object.keys(data).length) {
        window.LIVEDEV_SHOWCASE = data;
        document.dispatchEvent(new CustomEvent('livedev:showcase', { detail: data }));
      }
    } catch (e) {
      window.LIVEDEV_SHOWCASE = null;
    }
  };

  window.LiveDevAPI = {
    sessionKey,
    postLead: (payload) => postJson('/leads/', payload),
    loadSettings,
    loadShowcase,
    track: sendBeacon,
    reachGoal,
    reportLeadConversion: () => {
      const settings = window.LIVEDEV_SETTINGS || {};
      window.dataLayer = window.dataLayer || [];
      window.dataLayer.push({ event: 'livedev_lead_submit' });
      if (settings.google_tag_manager_id) return;
      if (typeof window.gtag === 'function') window.gtag('event', 'generate_lead');
      const id = settings.google_ads_id;
      const label = settings.google_ads_conversion_label;
      if (!id || !label || typeof window.gtag !== 'function') return;
      window.gtag('event', 'conversion', { send_to: `${id}/${label}` });
    },
  };

  document.addEventListener('DOMContentLoaded', () => {
    loadSettings().then(() => sendBeacon('view'));
    if (document.getElementById('productShowcase')) loadShowcase();
    // Enough for useful duration statistics without writing to PostgreSQL too often.
    setInterval(() => sendBeacon('heartbeat'), 30000);

    document.querySelectorAll('a[href^="#"]').forEach((a) => {
      a.addEventListener('click', () => {
        setTimeout(() => sendBeacon('section', { payload: { hash: location.hash } }), 50);
      });
    });

    window.addEventListener('pagehide', () => sendBeacon('leave'));
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') sendBeacon('heartbeat');
    });
  });
})();
