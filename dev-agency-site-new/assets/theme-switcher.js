(function () {
  const STORAGE_KEY = 'livedev-theme';
  const THEMES = [
    { id: 'dark', label: 'Тёмная' },
    { id: 'light', label: 'Светлая' },
    { id: 'ocean', label: 'Океан' },
  ];
  const ALLOWED = new Set(THEMES.map((t) => t.id));

  const root = document.documentElement;
  const toggle = document.getElementById('themeSwitcherToggle');
  if (!toggle) return;

  const saved = root.getAttribute('data-theme');
  let index = Math.max(0, THEMES.findIndex((t) => t.id === (ALLOWED.has(saved) ? saved : 'dark')));

  const label = (theme) => {
    toggle.setAttribute('aria-label', `Тема: ${theme.label}. Нажмите, чтобы сменить`);
    toggle.title = theme.label;
  };

  toggle.addEventListener('click', (event) => {
    event.stopPropagation();
    index = (index + 1) % THEMES.length;
    const theme = THEMES[index];
    root.setAttribute('data-theme', theme.id);
    label(theme);
    try { localStorage.setItem(STORAGE_KEY, theme.id); } catch (e) {}
  });

  label(THEMES[index]);
  if (!ALLOWED.has(saved)) {
    try { localStorage.setItem(STORAGE_KEY, THEMES[index].id); } catch (e) {}
  }
})();
