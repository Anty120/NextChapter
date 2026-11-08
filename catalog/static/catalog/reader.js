/* Reader chrome. Native anchors, the [popover] table of contents and the bookmark
   form all work without JS; this file adds focus handling, the sliding sheet,
   the current-chapter label, reading progress and in-place bookmark saving. */
(() => {
  const prose = document.querySelector('.story-text');
  if (!prose) return;
  const M = window.Motion;
  const UI = window.NextChapterUI;
  const reduced = () => (UI ? UI.reduced() : window.matchMedia('(prefers-reduced-motion: reduce)').matches);

  // Keyboard readers land on the chosen paragraph, not just scroll to it.
  function focusParagraph() {
    if (!/^#paragraph-\d+$/.test(location.hash)) return;
    const target = document.getElementById(location.hash.slice(1));
    if (target && prose.contains(target)) target.focus({ preventScroll: true });
  }
  window.addEventListener('hashchange', focusParagraph);
  focusParagraph();

  /* Swap a short label by blurring out, changing the text, blurring back in.
     Blur bridges the two states so they read as one changing object (Emil Kowalski). */
  function swapText(el, text) {
    if (!el || el.textContent === text) return;
    if (!M || reduced()) { el.textContent = text; return; }
    M.animate(el, { opacity: 0, filter: 'blur(4px)' }, UI.QUICK).finished.then(() => {
      el.textContent = text;
      UI.clearFilter(M.animate(el, { opacity: 1, filter: 'blur(0px)' }, { duration: 0.22, ease: 'easeOut' }), el);
    }, () => { el.textContent = text; });
  }

  /* ---------- Table of contents sheet ---------- */
  const toc = document.getElementById('toc');
  const trigger = document.querySelector('[popovertarget="toc"]:not([popovertargetaction="hide"])');
  const links = toc ? [...toc.querySelectorAll('a[href^="#paragraph-"]')] : [];
  const label = document.querySelector('[data-toc-current]');
  let current = -1;
  if (toc && typeof toc.showPopover === 'function') {
    UI?.glide(toc, '.menu-item');
    // A sheet slides from its edge with no overshoot (a bounce would open a gap at the edge).
    const SHEET = { type: 'spring', visualDuration: 0.36, bounce: 0 };
    let keyboard = false;
    trigger?.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') keyboard = true; });
    trigger?.addEventListener('pointerdown', () => { keyboard = false; });
    toc.addEventListener('beforetoggle', (event) => {
      if (event.newState === 'open') return;
      trigger?.setAttribute('aria-expanded', 'false');
      if (!M) return;
      if (reduced()) M.animate(toc, { opacity: 0 }, UI.QUICK);
      else M.animate(toc, { transform: 'translateX(-100%)' }, { duration: 0.22, ease: [0.32, 0.72, 0, 1] });
    });
    toc.addEventListener('toggle', (event) => {
      if (event.newState !== 'open') return;
      trigger?.setAttribute('aria-expanded', 'true');
      const here = links[current];
      if (here) here.scrollIntoView({ block: 'center' });
      if (M) {
        if (reduced()) { toc.style.transform = ''; M.animate(toc, { opacity: [0, 1] }, UI.FADE); }
        else {
          toc.style.opacity = '';
          // From where it is: closed, or caught halfway out (interruptible).
          if (!toc.style.transform) toc.style.transform = 'translateX(-100%)';
          M.animate(toc, { transform: 'translateX(0%)' }, SHEET);
          // The chapter rows follow the sheet in, 30ms apart, out of a 4px blur.
          const rows = links.slice(Math.max(0, current - 3), Math.max(0, current - 3) + 12);
          rows.forEach((row, i) => UI.clearFilter(M.animate(row, { opacity: [0, 1], filter: ['blur(4px)', 'blur(0px)'], transform: ['translateX(-8px)', 'translateX(0px)'] },
            { duration: 0.4, delay: 0.06 + i * 0.03, ease: [0.16, 1, 0.3, 1] }), row));
        }
      }
      if (keyboard || trigger?.matches(':focus-visible')) (here || links[0])?.focus();
    });
    // Choosing a chapter closes the sheet, then jumps and focuses the paragraph.
    links.forEach((link) => link.addEventListener('click', (event) => {
      event.preventDefault();
      toc.hidePopover();
      const hash = link.getAttribute('href');
      if (location.hash === hash) {
        document.getElementById(hash.slice(1))?.scrollIntoView({ block: 'start' });
        focusParagraph();
      } else {
        location.hash = hash;
      }
    }));
  }

  // Current chapter: watch only chapter starts crossing a band under the reader bar.
  const marks = links.map((a) => document.getElementById(a.getAttribute('href').slice(1)));
  function setCurrent(index) {
    if (index === current) return;
    links[current]?.removeAttribute('aria-current');
    current = index;
    if (links[current]) links[current].setAttribute('aria-current', 'location');
    swapText(label, links[current] ? `· ${links[current].textContent.trim()}` : '');
  }
  if (marks.length && marks.every(Boolean) && 'IntersectionObserver' in window) {
    let initial = -1;
    marks.forEach((mark, i) => { if (mark.getBoundingClientRect().top < 120) initial = i; });
    setCurrent(initial);
    const io = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        const i = marks.indexOf(entry.target);
        if (entry.isIntersecting) setCurrent(i);
        else if (entry.boundingClientRect.top > 0 && i === current) setCurrent(i - 1);
      }
    }, { rootMargin: '-90px 0px -62% 0px' });
    marks.forEach((mark) => io.observe(mark));
  }

  /* ---------- Reading progress ----------
     Motion's scroll() drives a scaleX animation from the prose's scroll position;
     where the browser supports ScrollTimeline it runs on the compositor. */
  const bar = document.querySelector('.read-progress span');
  if (bar) {
    if (M?.scroll) {
      M.scroll(M.animate(bar, { transform: ['scaleX(0)', 'scaleX(1)'] }, { ease: 'linear' }), { target: prose, offset: ['start 90px', 'end end'] });
    } else {
      let raf = 0;
      const update = () => {
        raf = 0;
        const r = prose.getBoundingClientRect();
        const p = Math.min(1, Math.max(0, (90 - r.top) / Math.max(1, r.height - window.innerHeight + 90)));
        bar.style.transform = `scaleX(${p})`;
      };
      window.addEventListener('scroll', () => { if (!raf) raf = requestAnimationFrame(update); }, { passive: true });
      update();
    }
  }

  /* ---------- Bookmarks save in place ----------
     The form still posts normally without JS (and as a fallback). With JS it saves
     with fetch, moves the ribbon to the new paragraph and keeps your scroll position:
     no reload of a 1,200-paragraph book. The view already answers JSON for this. */
  const form = document.querySelector('form.bookmarks');
  form?.addEventListener('submit', async (event) => {
    const button = event.submitter;
    if (!button?.classList.contains('bookmark') || form.dataset.native) return;
    event.preventDefault();
    if (button.getAttribute('aria-busy')) return;
    button.setAttribute('aria-busy', 'true');
    const body = new FormData(form);
    body.set('paragraph', button.value);
    try {
      const response = await fetch(form.action, { method: 'POST', body, credentials: 'same-origin', headers: { Accept: 'application/json' } });
      if (!response.ok || !(response.headers.get('content-type') || '').includes('application/json')) throw new Error('save failed');
      const section = button.closest('.paragraph');
      const previous = prose.querySelector('.saved-paragraph');
      if (previous && previous !== section) {
        previous.classList.remove('saved-paragraph');
        swapText(previous.querySelector('.bookmark-label'), 'Save my place');
      }
      section.classList.add('saved-paragraph');
      swapText(button.querySelector('.bookmark-label'), 'Saved here');
      document.querySelectorAll('.saved-link').forEach((link) => link.setAttribute('href', `#${section.id}`));
      UI?.toast('Your place is saved.');
    } catch {
      // Session expired or offline: fall back to the ordinary form post.
      form.dataset.native = '1';
      button.removeAttribute('aria-busy');
      form.requestSubmit(button);
      return;
    }
    button.removeAttribute('aria-busy');
  });
})();
