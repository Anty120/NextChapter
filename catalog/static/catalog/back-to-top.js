(() => {
  'use strict';
  const button = document.getElementById('back-to-top');
  if (!button) return;
  let frame = null;
  const update = () => {
    frame = null;
    button.hidden = window.scrollY <= 0 || document.documentElement.scrollHeight <= window.innerHeight + 1;
  };
  const schedule = () => { if (frame === null) frame = requestAnimationFrame(update); };
  window.addEventListener('scroll', schedule, {passive: true});
  window.addEventListener('resize', schedule);
  window.addEventListener('pageshow', schedule);
  // Content expansion, fonts and images may change whether the page can scroll.
  if (typeof ResizeObserver === 'function') new ResizeObserver(schedule).observe(document.body);
  button.addEventListener('click', () => {
    const top = document.querySelector('.topbar .brand') || document.getElementById('main');
    top?.focus({preventScroll: true});
    window.scrollTo({top: 0, behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth'});
  });
  update();
})();
