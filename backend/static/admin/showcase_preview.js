(function () {
  function parsePoints(raw) {
    return String(raw || '')
      .split(/[\n,]+/)
      .map(function (s) { return s.trim(); })
      .filter(Boolean)
      .slice(0, 3);
  }

  function paint() {
    var root = document.getElementById('ld-card-preview');
    if (!root) return;

    var titleEl = document.getElementById('id_title');
    var textEl = document.getElementById('id_text');
    var pointsEl = document.getElementById('id_points');

    var titleOut = root.querySelector('[data-pv="title"]');
    var textOut = root.querySelector('[data-pv="text"]');
    var pointsOut = root.querySelector('[data-pv="points"]');

    if (titleOut && titleEl) titleOut.textContent = titleEl.value || '—';
    if (textOut && textEl) textOut.textContent = textEl.value || '';

    if (pointsOut && pointsEl) {
      pointsOut.replaceChildren();
      parsePoints(pointsEl.value).forEach(function (p) {
        var span = document.createElement('span');
        span.textContent = p;
        pointsOut.appendChild(span);
      });
    }
  }

  function bind() {
    ['id_title', 'id_text', 'id_points'].forEach(function (id) {
      var el = document.getElementById(id);
      if (!el) return;
      el.addEventListener('input', paint);
      el.addEventListener('change', paint);
    });
    paint();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bind);
  } else {
    bind();
  }
})();
