/* Progressive enhancement. Content stays readable if Motion or JS is unavailable. */
(() => {
  'use strict';
  const motion = window.Motion;
  if (!motion?.animate) return;
  const preference = window.matchMedia('(prefers-reduced-motion: reduce)');
  const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)');
  const active = new Map();
  const frames = new Set();
  const interactive = '.book-card, .club-card, .more > a, .button, .nav a, #back-to-top';
  function animate(node, keyframes, options = {}) {
    if (preference.matches || !node?.isConnected) return;
    active.get(node)?.stop();
    const animation = motion.animate(node, keyframes, {duration:0.32, ...options});
    active.set(node, animation);
    Promise.resolve(animation).then(() => { if (active.get(node) === animation) active.delete(node); });
  }
  const spring = {type:'spring', stiffness:360, damping:27, mass:0.7};
  function position(node) {
    if (preference.matches || node.disabled) return;
    const pressed = node.dataset.uiPressed === 'true';
    const lifted = node.matches(':focus-visible') || (finePointer.matches && node.matches(':hover'));
    const card = node.matches('.book-card, .club-card, .more > a');
    animate(node, {y: pressed ? 1 : lifted && card ? -5 : 0, scale: pressed ? 0.975 : 1}, spring);
  }
  function gesture(node) {
    node.addEventListener('pointerenter', () => position(node));
    node.addEventListener('pointerleave', () => { delete node.dataset.uiPressed; position(node); });
    node.addEventListener('pointerdown', event => {
      if (event.button !== 0 || node.disabled) return;
      node.dataset.uiPressed = 'true'; position(node);
    });
    node.addEventListener('focus', () => position(node));
    node.addEventListener('blur', () => { delete node.dataset.uiPressed; position(node); });
    node.addEventListener('keydown', event => {
      if (event.repeat || !['Enter', ' '].includes(event.key) || (event.key === ' ' && node.tagName === 'A')) return;
      node.dataset.uiPressed = 'true'; position(node);
    });
    node.addEventListener('keyup', () => { delete node.dataset.uiPressed; position(node); });
  }
  document.querySelectorAll(interactive).forEach(gesture);
  const release = () => document.querySelectorAll('[data-ui-pressed]').forEach(node => { delete node.dataset.uiPressed; position(node); });
  window.addEventListener('pointerup', release);
  window.addEventListener('pointercancel', release);
  window.addEventListener('blur', release);
  let observer = null;
  function applyPreference() {
    observer?.disconnect();
    active.forEach(animation => animation.cancel()); active.clear();
    frames.forEach(node => { node.style.removeProperty('opacity'); node.style.removeProperty('transform'); });
    document.documentElement.dataset.uiMotion = preference.matches ? 'reduced' : 'enabled';
    if (preference.matches) return;
    // Never shift restored reading positions or hash-linked paragraph targets.
    if (window.scrollY < 2 && !location.hash) {
      const title = document.querySelector('.heading > div, .media-header, .club-hero, .auth');
      if (title) { frames.add(title); animate(title, {opacity:[0.7,1], y:[10,0]}, {...spring, stiffness:190, damping:24}); }
    }
    if ('IntersectionObserver' in window) {
      observer = new IntersectionObserver(entries => {
        let order = 0;
        entries.forEach(entry => {
          if (!entry.isIntersecting) return;
          observer.unobserve(entry.target); frames.add(entry.target);
          animate(entry.target, {opacity:[0.65,1]}, {duration:0.24, delay:Math.min(order++, 4)*0.035});
        });
      }, {threshold:0.08});
      document.querySelectorAll('.book-card, .club-card, .more > a').forEach(node => observer.observe(node));
    }
  }
  // Animate only the requested UI feedback, never paragraphs or popup position.
  const feedback = ['assist-panel','assist-result','practice-panel','practice-results','back-to-top'];
  feedback.forEach(id => {
    const node = document.getElementById(id);
    if (!node) return;
    new MutationObserver(() => {
      if (node.hidden) { active.get(node)?.cancel(); active.delete(node); return; }
      frames.add(node); animate(node, {opacity:[0.65,1]}, {duration:0.16});
    }).observe(node, {attributes:true, attributeFilter:['hidden']});
  });
  const translations = document.querySelectorAll('.translation-result');
  translations.forEach(node => new MutationObserver(() => {
    if (!node.hidden) { frames.add(node); animate(node, {opacity:[0.65,1]}, {duration:0.18}); }
  }).observe(node, {attributes:true, attributeFilter:['hidden']}));
  const submit = document.querySelector('form.tools');
  submit?.addEventListener('submit', () => { submit.setAttribute('aria-busy','true'); });
  window.addEventListener('pageshow', () => submit?.removeAttribute('aria-busy'));
  preference.addEventListener('change', applyPreference);
  applyPreference();
})();
