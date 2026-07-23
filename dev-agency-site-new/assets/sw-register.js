(function () {
  /* Service Worker выключен: ломал локальную скорость и смену тем.
     Включён позже только на проде, после проверки Performance. */
  if (!('serviceWorker' in navigator)) return;
  navigator.serviceWorker.getRegistrations().then((regs) => {
    regs.forEach((r) => r.unregister());
  });
})();
