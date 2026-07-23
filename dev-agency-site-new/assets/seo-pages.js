(function () {
  const form = document.getElementById('leadForm');
  if (!form) return;

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const data = new FormData(form);
    const button = form.querySelector('button[type="submit"]');
    const previous = button?.textContent;
    if (button) { button.disabled = true; button.textContent = 'Отправка…'; }
    try {
      await window.LiveDevAPI.postLead({
        name: String(data.get('name') || '').trim(),
        contact: String(data.get('contact') || '').trim(),
        message: String(data.get('message') || '').trim(),
        company_website: String(data.get('company_website') || '').trim(),
        page_url: location.href,
        source: 'seo_service_page',
      });
      window.LiveDevAPI.reachGoal?.(window.LIVEDEV_SETTINGS?.lead_goal_name || 'lead_submit');
      window.LiveDevAPI.reportLeadConversion?.();
      form.reset();
      alert('Заявка отправлена. Мы свяжемся с вами.');
    } catch (error) {
      alert('Не удалось отправить заявку. Напишите нам в Telegram или на email.');
    } finally {
      if (button) { button.disabled = false; button.textContent = previous || 'Получить оценку'; }
    }
  });
})();
