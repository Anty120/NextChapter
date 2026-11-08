/* On-demand comment translation. Original text and spoiler disclosure stay intact. */
(() => {
  'use strict';
  const preference = 'nextchapter:translation-language';
  document.querySelectorAll('.comment-translation').forEach(form => {
    const select = form.querySelector('select'), button = form.querySelector('button');
    const status = form.querySelector('.translation-status'), result = form.querySelector('.translation-result');
    const text = form.querySelector('.translation-text'), label = form.querySelector('.translation-label');
    const cache = new Map(); let request = null, generation = 0;
    try {
      const saved = localStorage.getItem(preference);
      if (saved && Array.from(select.options).some(option => option.value === saved)) select.value = saved;
    } catch (_) { /* Translation works when browser storage is unavailable. */ }
    const reset = () => {
      request?.abort(); request = null; generation++;
      button.disabled = select.disabled; button.removeAttribute('aria-busy');
      button.textContent = 'Translate'; button.setAttribute('aria-expanded', 'false');
      result.hidden = true; text.textContent = ''; status.textContent = '';
    };
    select.addEventListener('change', () => {
      reset(); try { localStorage.setItem(preference, select.value); } catch (_) { /* Optional preference only. */ }
    });
    form.addEventListener('submit', async event => {
      event.preventDefault();
      if (button.disabled || select.disabled || request) return;
      if (!result.hidden) { result.hidden = true; button.textContent = 'Show translation'; button.setAttribute('aria-expanded', 'false'); return; }
      const target = select.value, token = ++generation;
      const show = translation => {
        text.textContent = translation; text.lang = target;
        label.textContent = `Translation · ${select.selectedOptions[0].textContent}`;
        result.hidden = false; status.textContent = '';
        button.textContent = 'Hide translation'; button.setAttribute('aria-expanded', 'true');
      };
      if (cache.has(target)) { show(cache.get(target)); return; }
      request = new AbortController(); button.disabled = true; button.setAttribute('aria-busy', 'true');
      status.textContent = 'Translating…';
      try {
        const response = await fetch(form.dataset.translationUrl, {
          method: 'POST', credentials: 'same-origin', signal: request.signal,
          headers: {'Content-Type': 'application/json', 'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value},
          body: JSON.stringify({target_language: target}),
        });
        let data; try { data = await response.json(); } catch (_) { /* Use the status fallback. */ }
        if (!response.ok) throw new Error(data?.error?.message || (response.status === 403 ? 'Refresh this page and try again.' : 'Translation is unavailable. Please try again.'));
        if (typeof data?.translation !== 'string' || !data.translation.trim()) throw new Error('Translation could not finish. Please try again.');
        if (token !== generation) return;
        cache.set(target, data.translation); show(data.translation);
      } catch (error) {
        if (token === generation && error.name !== 'AbortError') {
          status.textContent = navigator.onLine === false ? 'You are offline. Reconnect and try Translate again.' : error.message;
          button.textContent = 'Retry translation';
        }
      } finally {
        if (token === generation) { request = null; button.disabled = select.disabled; button.removeAttribute('aria-busy'); }
      }
    });
    window.addEventListener('pagehide', () => request?.abort());
  });
})();
