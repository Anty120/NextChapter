/* Native anchors work without JS; focus the chosen paragraph for keyboard readers. */
(() => {
  const prose = document.querySelector('.story-text');
  if (!prose) return;
  function focusParagraph() {
    if (!/^#paragraph-\d+$/.test(location.hash)) return;
    const target = document.getElementById(location.hash.slice(1));
    if (target && prose.contains(target)) target.focus({ preventScroll: true });
  }
  window.addEventListener('hashchange', focusParagraph);
  focusParagraph();
})();
