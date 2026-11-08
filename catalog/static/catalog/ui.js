/* NextChapter motion layer (Motion 14, vendored as window.Motion).
   Progressive enhancement only: every control here already works without this file.
   Popovers are native [popover], forms submit normally, links are links.

   Rules, taken from docs/reviews/motion-redesign/README.md:
   - Three springs, reused everywhere, so the whole app has one physical feel.
   - Blur is a verb: elements blur in and out while moving, never at rest.
   - Exits are faster than entrances; every animation can be interrupted mid-flight
     (Motion retargets from the current value and keeps velocity).
   - prefers-reduced-motion: no transforms, no blur, short opacity fades only. */
(() => {
  const M = window.Motion;
  const root = document.documentElement;
  const reduceQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
  const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)');
  const reduced = () => reduceQuery.matches;

  // Spring presets, as Motion's duration + bounce (Bencho: consistency from reuse).
  const SPRING = {
    // Functional UI that must feel instant: the travelling highlight, press-down.
    snappy: { type: 'spring', visualDuration: 0.22, bounce: 0 },
    // Panels, popovers and cards settling into place: a whisper of overshoot.
    settle: { type: 'spring', visualDuration: 0.32, bounce: 0.12 },
    // Stickers and confirmations (LifeVal's sticker spring): reads as a slap, not a boing.
    slap: { type: 'spring', visualDuration: 0.34, bounce: 0.18 },
  };
  const QUICK = { duration: 0.14, ease: [0.23, 1, 0.32, 1] }; // exits: faster than any entrance
  const FADE = { duration: 0.18, ease: 'easeOut' };

  root.classList.add('ui-ready');
  if (M) {
    root.classList.add('motion');
    // Exposes the live motion mode (also read by scripts/check_motion_browser.py).
    const mark = () => { root.dataset.uiMotion = reduceQuery.matches ? 'reduced' : 'enabled'; };
    mark();
    reduceQuery.addEventListener('change', mark);
  }

  /* Animate with Motion when we can; otherwise jump to the end state.
     Under reduced motion, only opacity animates and everything else snaps. */
  function play(el, keyframes, transition = SPRING.settle) {
    if (!el) return null;
    const last = (v) => (Array.isArray(v) ? v[v.length - 1] : v);
    if (!M || reduced()) {
      // Every transform/filter/clip end state used in this app is the element's resting
      // style, so returning to it (clearing the inline value) is the motionless version.
      for (const key in keyframes) if (key !== 'opacity') el.style[key] = '';
      if ('opacity' in keyframes) {
        if (M) return M.animate(el, { opacity: keyframes.opacity }, FADE);
        el.style.opacity = last(keyframes.opacity);
      }
      return null;
    }
    return M.animate(el, keyframes, transition);
  }
  // Blur ends at blur(0px); drop it afterwards so nothing rests with a filter layer.
  function clearFilter(animation, el) {
    animation?.finished?.then(() => { if (el.style.filter === 'blur(0px)') el.style.filter = ''; }, () => {});
  }
  window.NextChapterUI = { play, clearFilter, SPRING, QUICK, FADE, reduced, toast, glide: (...args) => glide(...args) };

  /* ---------- Toasts ----------
     Django messages arrive as <p class="toast">. They spring up from the bottom edge
     with a small blur, wait, and leave the way they came (exit path = entry path). */
  const region = document.querySelector('.messages');
  function dismiss(el) {
    if (!el.isConnected || el.dataset.leaving) return;
    el.dataset.leaving = '1';
    const siblings = [...region.children].filter((t) => t !== el);
    const before = siblings.map((t) => t.getBoundingClientRect().top);
    const out = play(el, { opacity: 0, transform: 'translateY(16px) scale(.97)', filter: 'blur(4px)' }, { ...QUICK, filter: QUICK });
    const remove = () => {
      el.remove();
      // FLIP the remaining toasts into their new places instead of letting them jump.
      const after = siblings.map((t) => t.getBoundingClientRect().top);
      siblings.forEach((t, i) => {
        const dy = before[i] - after[i];
        if (dy) play(t, { transform: [`translateY(${dy}px)`, 'translateY(0px)'] }, SPRING.settle);
      });
    };
    if (out?.finished) out.finished.then(remove, remove); else remove();
  }
  function arm(el) {
    if (el.dataset.armed) return;
    el.dataset.armed = '1';
    const text = el.textContent.trim();
    el.textContent = '';
    const span = document.createElement('span');
    span.className = 'toast-text';
    span.textContent = text;
    const close = document.createElement('button');
    close.type = 'button';
    close.className = 'toast-close';
    close.setAttribute('aria-label', 'Dismiss message');
    close.textContent = '×';
    close.addEventListener('click', () => dismiss(el));
    el.append(span, close);
    clearFilter(play(el, { opacity: [0, 1], transform: ['translateY(24px) scale(.96)', 'translateY(0px) scale(1)'], filter: ['blur(6px)', 'blur(0px)'] },
      { ...SPRING.slap, opacity: FADE, filter: { duration: 0.25 } }), el);
    // Long enough to read (WCAG 2.2.1); paused while pointed at or focused.
    let remaining = Math.max(5200, text.length * 70);
    let started = Date.now();
    let timer = setTimeout(() => dismiss(el), remaining);
    const pause = () => { clearTimeout(timer); remaining -= Date.now() - started; };
    const resume = () => { started = Date.now(); timer = setTimeout(() => dismiss(el), Math.max(remaining, 1500)); };
    el.addEventListener('pointerenter', pause);
    el.addEventListener('pointerleave', resume);
    el.addEventListener('focusin', pause);
    el.addEventListener('focusout', resume);
  }
  function toast(text, tone = 'success') {
    if (!region) return;
    const el = document.createElement('p');
    el.className = `toast toast-${tone}`;
    el.textContent = text;
    region.append(el);
    arm(el);
  }
  region?.querySelectorAll('.toast').forEach(arm);

  /* ---------- The travelling highlight ----------
     noechague.com: one highlight object slides between rows on a spring instead of
     every row fading its own background. Clip-path inset keeps the rounded corners
     exact while it moves, and costs no layout. Used by the nav and every menu. */
  function glide(container, itemSelector) {
    if (!M) return;
    const glider = document.createElement('span');
    glider.className = 'glider';
    glider.setAttribute('aria-hidden', 'true');
    container.prepend(glider);
    let shown = false;
    const clipFor = (item) => {
      const c = container.getBoundingClientRect();
      const r = item.getBoundingClientRect();
      const top = r.top - c.top; const left = r.left - c.left;
      return `inset(${top}px ${c.width - left - r.width}px ${c.height - top - r.height}px ${left}px round 6px)`;
    };
    const moveTo = (item) => {
      if (!item || item.getAttribute('aria-current') === 'page') { hide(); return; }
      const clip = clipFor(item);
      if (!shown || reduced()) {
        // First touch appears in place (no slide from nowhere), blurring in.
        glider.style.clipPath = clip;
        play(glider, { opacity: [0, 1] }, FADE);
      } else {
        M.animate(glider, { clipPath: clip }, SPRING.snappy);
      }
      shown = true;
    };
    const hide = () => { if (!shown) return; shown = false; play(glider, { opacity: 0 }, QUICK); };
    container.addEventListener('pointerover', (event) => {
      if (event.pointerType !== 'mouse' || !finePointer.matches) return;
      moveTo(event.target.closest(itemSelector));
    });
    container.addEventListener('pointerleave', hide);
    container.addEventListener('focusin', (event) => {
      if (event.target.matches(':focus-visible')) moveTo(event.target.closest(itemSelector));
    });
    container.addEventListener('focusout', (event) => { if (!container.contains(event.relatedTarget)) hide(); });
    return { hide };
  }
  document.querySelectorAll('.nav.glide').forEach((nav) => glide(nav, 'a'));

  /* ---------- Popovers that grow from their trigger ----------
     Native popover gives Esc, click-outside and focus return. We anchor it to the
     trigger, grow it from the trigger's corner on a spring, and shrink it out
     quickly. CSS keeps it rendered (display/overlay allow-discrete) during the exit. */
  const menuItems = (pop) => [...pop.querySelectorAll('.menu-item:not([hidden])')];
  function enhanceMenu(pop) {
    const trigger = document.querySelector(`[popovertarget="${pop.id}"]:not([popovertargetaction="hide"])`);
    if (!trigger) return;
    const glider = glide(pop, '.menu-item');
    let openedByKeyboard = false;
    let closing = false;
    let originY = 'top';
    function place() {
      const r = trigger.getBoundingClientRect();
      const vw = document.documentElement.clientWidth;
      const width = pop.offsetWidth || parseFloat(getComputedStyle(pop).minWidth) || 220;
      const below = window.innerHeight - r.bottom;
      const alignRight = r.left + r.width / 2 > vw / 2;
      originY = below < 260 && r.top > below ? 'bottom' : 'top';
      const s = pop.style;
      s.left = `${Math.max(8, Math.min(alignRight ? r.right - width : r.left, vw - width - 8))}px`;
      s.right = 'auto';
      s.top = originY === 'top' ? `${r.bottom + 8}px` : 'auto';
      s.bottom = originY === 'bottom' ? `${window.innerHeight - r.top + 8}px` : 'auto';
      s.transformOrigin = `${originY} ${alignRight ? 'right' : 'left'}`;
    }
    let raf = 0;
    function schedulePlace() {
      if (!pop.matches(':popover-open') || raf) return;
      raf = requestAnimationFrame(() => {
        raf = 0;
        if (pop.matches(':popover-open')) place();
      });
    }
    const card = trigger.closest('.book-card');
    // Opening can catch the button's press spring and the card's hover lift mid-flight.
    // Re-anchor when they settle, without measuring layout on every animation frame.
    function placeAfterMotion() {
      const animations = [trigger, card].filter(Boolean).flatMap((el) => el.getAnimations());
      Promise.allSettled(animations.map((animation) => animation.finished)).then(schedulePlace);
    }
    card?.addEventListener('transitionend', (event) => { if (event.target === card) schedulePlace(); });
    card?.addEventListener('transitioncancel', (event) => { if (event.target === card) schedulePlace(); });
    trigger.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown') openedByKeyboard = true; });
    trigger.addEventListener('pointerdown', () => { openedByKeyboard = false; });
    pop.addEventListener('beforetoggle', (event) => {
      if (event.newState === 'open') {
        place();
        return;
      }
      trigger.setAttribute('aria-expanded', 'false');
      glider?.hide();
      const lift = originY === 'top' ? '-4px' : '4px';
      closing = true;
      const out = play(pop, { opacity: 0, transform: `translateY(${lift}) scale(.96)`, filter: 'blur(2px)' }, QUICK);
      const done = () => { closing = false; };
      if (out?.finished) out.finished.then(done, done); else done();
    });
    pop.addEventListener('toggle', (event) => {
      if (event.newState !== 'open') return;
      trigger.setAttribute('aria-expanded', 'true');
      const lift = originY === 'top' ? '-6px' : '6px';
      // If it was still shrinking out, spring back from where it is (interruptible).
      const from = !closing ? { opacity: [0, 1], transform: [`translateY(${lift}) scale(.9)`, 'translateY(0px) scale(1)'], filter: ['blur(4px)', 'blur(0px)'] }
        : { opacity: 1, transform: 'translateY(0px) scale(1)', filter: 'blur(0px)' };
      closing = false;
      clearFilter(play(pop, from, { ...SPRING.settle, opacity: FADE, filter: { duration: 0.2 } }), pop);
      if (openedByKeyboard || trigger.matches(':focus-visible')) menuItems(pop)[0]?.focus();
      placeAfterMotion();
    });
    // Arrow keys move between items; Home/End jump. Tab still leaves normally.
    pop.addEventListener('keydown', (event) => {
      const items = menuItems(pop);
      const i = items.indexOf(document.activeElement);
      const go = { ArrowDown: i + 1, ArrowUp: i - 1, Home: 0, End: items.length - 1 }[event.key];
      if (go === undefined || !items.length) return;
      event.preventDefault();
      items[(go + items.length) % items.length].focus();
    });
    // Keep it attached to its trigger while the page scrolls (read, then write once).
    window.addEventListener('scroll', schedulePlace, { passive: true });
    window.addEventListener('resize', () => { if (pop.matches(':popover-open')) pop.hidePopover(); });
  }
  const supportsPopover = typeof HTMLElement.prototype.showPopover === 'function';
  if (supportsPopover) document.querySelectorAll('.popover.menu[popover]').forEach(enhanceMenu);

  // Copy link (JS only, so the item is hidden until now).
  document.querySelectorAll('[data-copy-link]').forEach((button) => {
    if (!navigator.clipboard) return;
    button.hidden = false;
    button.addEventListener('click', async () => {
      const url = new URL(button.dataset.copyLink, window.location.href).href;
      button.closest('[popover]')?.hidePopover();
      try { await navigator.clipboard.writeText(url); toast('Link copied. Share it with a friend.', 'info'); }
      catch { toast('Could not copy the link. Open the item and copy it from the address bar.', 'error'); }
    });
  });

  /* ---------- Press feedback ----------
     Motion's press() handles pointer and keyboard presses alike. Down is quick and
     firm; release springs back with a little bounce, so it reads as a physical press. */
  if (M) {
    const pressable = '.button, .icon-button, .chip, .menu-item, .deck-play, .deck-skips button, .bookmark, .account-trigger, .toast-close';
    M.press(pressable, (el) => {
      if (reduced()) return undefined;
      const depth = el.matches('.chip, .menu-item') ? 0.97 : 0.95;
      M.animate(el, { transform: `scale(${depth})` }, SPRING.snappy);
      return () => M.animate(el, { transform: 'scale(1)' }, SPRING.slap);
    });
    M.press('.book-card', (el, event) => {
      if (reduced() || event.target.closest('.icon-button')) return undefined;
      M.animate(el, { transform: 'scale(.985)' }, SPRING.snappy);
      return () => M.animate(el, { transform: 'scale(1)' }, SPRING.slap);
    });
  }

  /* ---------- Format chips: one thumb travels between options ---------- */
  document.querySelectorAll('.chips').forEach((group) => {
    const row = group.querySelector('.chip-row');
    const thumb = group.querySelector('.chip-thumb');
    if (!row || !thumb || !M) return;
    group.classList.add('has-thumb');
    const clipFor = (chip) => {
      const w = row.scrollWidth; const h = row.clientHeight;
      const left = chip.offsetLeft - 3; const top = chip.offsetTop - 3;
      return `inset(${top}px ${w - 6 - left - chip.offsetWidth}px ${h - 6 - top - chip.offsetHeight}px ${left}px round 4px)`;
    };
    thumb.style.inset = '3px auto 3px 3px';
    const current = () => row.querySelector('input:checked')?.closest('.chip');
    // Read layout first, then write, so a resize never forces a synchronous reflow.
    const snap = () => {
      const width = `${row.scrollWidth - 6}px`;
      const c = current(); const clip = c ? clipFor(c) : '';
      thumb.style.width = width;
      if (clip) thumb.style.clipPath = clip;
    };
    // ResizeObserver reports after layout, so measuring here never forces a reflow.
    if ('ResizeObserver' in window) new ResizeObserver(snap).observe(row); else snap();
    row.addEventListener('change', () => {
      const chip = current();
      if (!chip) return;
      if (reduced()) { thumb.style.clipPath = clipFor(chip); return; }
      M.animate(thumb, { clipPath: clipFor(chip) }, SPRING.settle);
      chip.scrollIntoView({ block: 'nearest', inline: 'nearest' });
    });
  });

  /* ---------- Shelf: cards dealt out as they scroll into view ----------
     LifeVal's photo collage: each card arrives from a little lower and smaller,
     already at its resting tilt, in reading order, 40ms apart. Cards above the
     fold are covered by the CSS reveal, so nothing visible is ever hidden by JS. */
  const cards = [...document.querySelectorAll('.story-grid .book-card')];
  if (M && cards.length && !reduced() && 'IntersectionObserver' in window) {
    // The observer's first report says which cards start off-screen, without the
    // script measuring layout itself (no forced reflow at load).
    const seen = new WeakSet();
    let queue = [];
    let scheduled = false;
    const flush = () => {
      scheduled = false;
      // At most four cards blur in together; blurred layers are the expensive part.
      const batch = queue.splice(0, 4);
      if (queue.length) { scheduled = true; setTimeout(() => requestAnimationFrame(flush), 120); }
      batch.forEach((card, i) => {
        clearFilter(M.animate(card, { opacity: 1, transform: 'translateY(0px) scale(1)', filter: 'blur(0px)' },
          { ...SPRING.settle, delay: i * 0.04, opacity: { duration: 0.3, delay: i * 0.04 }, filter: { duration: 0.35, delay: i * 0.04 } }), card);
      });
    };
    const io = new IntersectionObserver((entries) => {
      for (const { target: card, isIntersecting } of entries) {
        if (!seen.has(card)) {
          seen.add(card);
          if (isIntersecting) { io.unobserve(card); continue; } // on screen at load: the CSS reveal has it
          card.style.opacity = '0';
          card.style.transform = 'translateY(28px) scale(.94)';
          card.style.filter = 'blur(6px)';
          continue;
        }
        if (!isIntersecting) continue;
        io.unobserve(card);
        queue.push(card);
        if (!scheduled) { scheduled = true; requestAnimationFrame(flush); }
      }
    }, { threshold: 0.15 });
    cards.forEach((card) => io.observe(card));
  }
  // Without the CSS-hidden cards ever being stuck: anything focused is shown.
  document.addEventListener('focusin', (event) => {
    const card = event.target.closest?.('.book-card');
    if (card && card.style.opacity === '0') play(card, { opacity: 1, transform: 'translateY(0px) scale(1)', filter: 'blur(0px)' }, FADE);
  });

  /* ---------- Forms that reload the page: join, leave, post ----------
     The server round-trip stays a normal form post. While it is in flight the button
     says what is happening (and ignores double submits); when the page comes back,
     the result is acknowledged where it happened, not only in a toast. */
  const ARRIVAL = 'nextchapter:arrival';
  function relabel(button, text) {
    const label = button.childNodes[0];
    if (!label || label.nodeType !== Node.TEXT_NODE) return;
    button.dataset.label = button.dataset.label || label.textContent;
    play(button, { filter: ['blur(3px)', 'blur(0px)'], opacity: [0.6, 1] }, { duration: 0.22 });
    label.textContent = text;
  }
  document.querySelectorAll('form[data-pending]').forEach((form) => {
    form.addEventListener('submit', (event) => {
      if (form.dataset.busy) { event.preventDefault(); return; }
      form.dataset.busy = '1';
      const button = event.submitter || form.querySelector('[type=submit]');
      if (button) { button.setAttribute('aria-busy', 'true'); relabel(button, `${form.dataset.pending} `); }
      try { sessionStorage.setItem(ARRIVAL, JSON.stringify({ key: form.dataset.arrival, at: Date.now() })); } catch { /* storage off */ }
    });
  });
  // Coming back via the back button restores a frozen page: un-stick it.
  window.addEventListener('pageshow', (event) => {
    if (!event.persisted) return;
    document.querySelectorAll('form[data-busy]').forEach((form) => {
      delete form.dataset.busy;
      form.querySelectorAll('[aria-busy]').forEach((b) => { b.removeAttribute('aria-busy'); if (b.dataset.label && b.childNodes[0]) b.childNodes[0].textContent = b.dataset.label; });
    });
  });
  let arrival = null;
  try { arrival = JSON.parse(sessionStorage.getItem(ARRIVAL) || 'null'); sessionStorage.removeItem(ARRIVAL); } catch { arrival = null; }
  if (arrival && Date.now() - arrival.at < 30000) {
    const stamp = document.querySelector(`[data-stamp="${CSS.escape(arrival.key)}"]`);
    if (stamp) {
      // The membership badge is slapped on like a sticker (LifeVal: from 35% scale, 8deg under).
      play(stamp, { opacity: [0, 1], transform: ['scale(.35) rotate(-8deg) translateY(8px)', 'scale(1) rotate(0deg) translateY(0px)'] }, { ...SPRING.slap, opacity: FADE, delay: 0.25 });
    }
    const landing = document.querySelector(`[data-landing="${CSS.escape(arrival.key)}"]`);
    const firstComment = landing?.querySelector('.comment');
    if (firstComment && !document.querySelector('.comment-form .errorlist') && !new URLSearchParams(window.location.search).get('page')) {
      firstComment.classList.add('is-landing');
      clearFilter(play(firstComment, { opacity: [0, 1], transform: ['translateY(-10px)', 'translateY(0px)'], filter: ['blur(6px)', 'blur(0px)'] },
        { ...SPRING.settle, opacity: { duration: 0.3 }, filter: { duration: 0.35 }, delay: 0.2 }), firstComment);
    }
  }

  // Comment box: Ctrl/Cmd + Enter posts.
  document.querySelectorAll('.comment-form').forEach((form) => {
    const box = form.querySelector('textarea');
    const hint = form.querySelector('.comment-hint');
    if (!box) return;
    if (hint) { hint.hidden = false; if (/Mac|iPhone|iPad/.test(navigator.platform)) hint.textContent = '⌘ + Enter posts'; }
    box.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) { event.preventDefault(); form.requestSubmit(); }
    });
  });
})();
