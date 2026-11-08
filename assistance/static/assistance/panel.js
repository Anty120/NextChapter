(() => {
  'use strict';
  const root = document.getElementById('assistance-root');
  if (!root) return;
  const story = document.querySelector('.story-text[data-assist-media]') || document.querySelector('.story-text');
  const el = (id) => root.querySelector(`#assist-${id}`);
  const panel = el('panel');
  if (!panel) return;
  const yes = (value) => value === 'true' || value === '1';
  const authenticated = yes(root.dataset.authenticated);
  const enabled = yes(root.dataset.enabled);
  const allowed = authenticated && enabled;
  const paragraphs = story ? Array.from(story.querySelectorAll('[id^="paragraph-"]')).map((node) => ({node, prose: node.querySelector('p'), index: Number(node.id.slice(10))})).filter((p) => p.prose && Number.isInteger(p.index)) : [];
  let reference = null, opener = null, explainAbort = null, voiceAbort = null, generation = 0, voiceGeneration = 0;
  let voice = null, voiceUrl = null, voiceKey = '';
  const points = (s) => Array.from(s);
  const prefixLength = (text, offset) => points(text.slice(0, offset)).length;
  const locale = story?.dataset.assistLocale || root.dataset.targetLocale || 'en-US';
  const status = (message, error = false) => { el('status').textContent = message; el('status').classList.toggle('assist-error', error); };
  const stopVoice = (dispose = false) => {
    voiceAbort?.abort(); voiceAbort = null; voiceGeneration++;
    if (voice) { voice.pause(); voice.currentTime = 0; }
    if (dispose) { voice = null; if (voiceUrl) URL.revokeObjectURL(voiceUrl); voiceUrl = null; voiceKey = ''; }
  };
  const show = (moveFocus = true) => {
    if (panel.hidden) opener = document.activeElement;
    panel.hidden = false; el('open').setAttribute('aria-expanded', 'true');
    if (moveFocus) { el('title').focus(); panel.scrollIntoView({block: 'nearest'}); }
  };
  const close = () => {
    explainAbort?.abort(); generation++; stopVoice(); el('explain').removeAttribute('aria-busy');
    const practice = root.querySelector('#practice-panel'); if (practice) practice.hidden = true;
    panel.hidden = true; el('open').setAttribute('aria-expanded', 'false');
    if (opener instanceof HTMLElement && opener.isConnected && opener !== document.body) opener.focus(); else el('open').focus();
  };
  const csrf = () => root.querySelector('[name=csrfmiddlewaretoken]')?.value || document.cookie.split('; ').find((v) => v.startsWith('csrftoken='))?.slice(10) || '';
  const payload = () => reference && ({media_id: reference.media_id, paragraph: reference.paragraph, start: reference.start, end: reference.end, locale: reference.locale, explanation_locale: reference.explanation_locale});
  const errors = {401: 'Please log in again to use language help.', 403: 'Your session could not be verified. Refresh this page and retry.', 429: 'Language help is busy. Wait a moment, then retry.', 503: 'Language help is not configured or temporarily unavailable. You can continue reading.', 502: 'The language service could not finish. Please retry.'};
  const request = async (url, signal) => {
    if (!url) throw new Error('Language help is not configured. You can continue reading.');
    const response = await fetch(url, {method: 'POST', credentials: 'same-origin', headers: {'Content-Type': 'application/json', 'X-CSRFToken': decodeURIComponent(csrf()), Accept: 'application/json, audio/*'}, body: JSON.stringify(payload()), signal});
    if (!response.ok) {
      let data; try { data = await response.json(); } catch (_) { /* Status fallback remains useful. */ }
      throw new Error(data?.error?.message || errors[response.status] || 'That passage could not be explained. Choose a shorter passage or retry.');
    }
    return response;
  };
  function choose(p, start, end, moveFocus = true) {
    const text = p.prose.textContent;
    if (start < 0 || end <= start || end > points(text).length || end - start > 300) {
      explainAbort?.abort(); generation++; stopVoice(true); reference = null;
      el('result').hidden = true; el('actions').hidden = true; el('explain').disabled = true;
      show(moveFocus); status('Choose a word or sentence of at most 300 characters.', true); return false;
    }
    explainAbort?.abort(); generation++; stopVoice(true);
    reference = {media_id: Number(story.dataset.assistMedia || root.dataset.mediaId), paragraph: p.index, start, end, locale, explanation_locale: root.dataset.explanationLocale || 'en', selection: points(text).slice(start, end).join('')};
    el('selection').textContent = reference.selection; el('selection').lang = locale;
    el('result').hidden = true; el('actions').hidden = !allowed;
    el('paragraph').value = String(p.index); populatePassages(p, start, end);
    el('explain').disabled = !allowed; el('explain').removeAttribute('aria-busy');
    status(allowed ? 'Selection ready. Choose Explain selection, Listen, or Practice.' : ''); show(moveFocus); return true;
  }
  function segments(text, granularity) {
    if (typeof Intl.Segmenter === 'function') return Array.from(new Intl.Segmenter(locale, {granularity}).segment(text)).filter((s) => granularity !== 'word' || s.isWordLike).map((s) => ({text: s.segment, start: prefixLength(text, s.index), end: prefixLength(text, s.index + s.segment.length)}));
    const pattern = granularity === 'word' ? /[\p{L}\p{M}\p{N}]+(?:['’][\p{L}\p{M}]+)*/gu : /[^.!?]+[.!?]*/gu;
    return Array.from(text.matchAll(pattern), (m) => ({text: m[0], start: prefixLength(text, m.index), end: prefixLength(text, m.index + m[0].length)}));
  }
  function populatePassages(p, selectedStart, selectedEnd) {
    const select = el('passage'); select.replaceChildren();
    for (const [name, type] of [['Sentences', 'sentence'], ['Words', 'word']]) {
      const group = document.createElement('optgroup'); group.label = name;
      for (const part of segments(p.prose.textContent, type)) {
        if (part.end - part.start > 300 || !part.text.trim()) continue;
        const option = document.createElement('option'); option.value = `${part.start}:${part.end}`; option.textContent = part.text.trim(); option.selected = part.start === selectedStart && part.end === selectedEnd; group.append(option);
      }
      select.append(group);
    }
  }
  async function explain() {
    if (!reference || !allowed) return;
    explainAbort?.abort(); explainAbort = new AbortController(); const current = ++generation;
    status('Asking Gemini about this passage…'); el('result').hidden = true; el('explain').setAttribute('aria-busy', 'true');
    try {
      const data = await (await request(root.dataset.explainUrl, explainAbort.signal)).json();
      if (current !== generation) return;
      const list = el('definitions'); list.replaceChildren();
      for (const [key, label] of [['language', 'Language / variety'], ['meaning', 'Meaning in context'], ['translation', 'Translation'], ['ipa', 'IPA'], ['sound_guidance', 'Sound and mouth guidance'], ['approximation', 'Approximate sound comparison'], ['caveat', 'Limits'], ['uncertainty', 'Uncertainty']]) {
        if (typeof data[key] !== 'string' || !data[key]) continue;
        const term = document.createElement('dt'), detail = document.createElement('dd'); term.textContent = label; detail.textContent = data[key]; if (key === 'ipa') detail.lang = locale; list.append(term, detail);
      }
      const examples = el('examples'); examples.replaceChildren();
      for (const example of Array.isArray(data.examples) ? data.examples : []) {
        const li = document.createElement('li'), text = document.createElement('span'); text.lang = locale; text.textContent = typeof example.text === 'string' ? example.text : ''; li.append(text);
        if (typeof example.note === 'string') li.append(document.createTextNode(` — ${example.note}`)); examples.append(li);
      }
      el('result').hidden = false; status('Explanation ready. Gemini can make mistakes; sound comparisons are approximate.');
    } catch (error) { if (current === generation && error.name !== 'AbortError') status(navigator.onLine === false ? 'You are offline. Reconnect and choose Explain selection to retry.' : error.message, true); }
    finally { if (current === generation) el('explain').removeAttribute('aria-busy'); }
  }
  function captureSelection(moveFocus = true) {
    const selection = window.getSelection(); if (!selection || selection.isCollapsed || !selection.rangeCount) return false;
    const range = selection.getRangeAt(0);
    const p = paragraphs.find((part) => part.prose.contains(range.startContainer) && part.prose.contains(range.endContainer));
    if (!p) {
      if (story?.contains(range.startContainer) || story?.contains(range.endContainer)) {
        explainAbort?.abort(); generation++; stopVoice(true); reference = null;
        el('result').hidden = true; el('actions').hidden = true; el('explain').disabled = true;
        show(moveFocus); status('Choose text within one paragraph, up to 300 characters.', true);
      }
      return false;
    }
    const before = range.cloneRange(); before.selectNodeContents(p.prose); before.setEnd(range.startContainer, range.startOffset);
    const start = points(before.toString()).length, end = start + points(range.toString()).length;
    return choose(p, start, end, moveFocus);
  }
  el('open').addEventListener('click', () => { show(); if (!captureSelection(false) && !reference && paragraphs.length) el('passage').dispatchEvent(new Event('change')); });
  el('close').addEventListener('click', close);
  panel.addEventListener('keydown', (event) => { if (event.key === 'Escape') { event.preventDefault(); close(); } });
  el('explain').addEventListener('click', () => { captureSelection(false); explain(); });
  for (const p of paragraphs) { const option = document.createElement('option'); option.value = String(p.index); option.textContent = `Paragraph ${p.index + 1}: ${p.prose.textContent.slice(0, 65)}`; el('paragraph').append(option); }
  el('paragraph').addEventListener('change', () => { const p = paragraphs.find((p) => String(p.index) === el('paragraph').value); populatePassages(p); el('passage').dispatchEvent(new Event('change')); });
  el('passage').addEventListener('change', () => { const p = paragraphs.find((p) => String(p.index) === el('paragraph').value); const [start, end] = el('passage').value.split(':').map(Number); if (p) choose(p, start, end, false); });
  story?.addEventListener('pointerup', () => {
    if (window.getSelection()?.toString().trim() && captureSelection(false)) status('Text selected. Choose Explain selection.');
  });
  story?.addEventListener('click', (event) => {
    if (event.target.closest('a,button,input,select,form') || window.getSelection()?.toString().trim()) return;
    const p = paragraphs.find((p) => p.prose.contains(event.target)); if (!p) return;
    let node, offset;
    if (document.caretPositionFromPoint) { const caret = document.caretPositionFromPoint(event.clientX, event.clientY); node = caret?.offsetNode; offset = caret?.offset; }
    else if (document.caretRangeFromPoint) { const caret = document.caretRangeFromPoint(event.clientX, event.clientY); node = caret?.startContainer; offset = caret?.startOffset; }
    if (!node || !p.prose.contains(node)) return;
    const before = document.createRange(); before.selectNodeContents(p.prose); before.setEnd(node, offset); const at = points(before.toString()).length;
    const word = segments(p.prose.textContent, 'word').find((s) => at >= s.start && at < s.end);
    if (word && choose(p, word.start, word.end)) explain();
  });
  el('listen').addEventListener('click', async () => {
    if (!reference || !allowed) return;
    const key = JSON.stringify(payload()); stopVoice(); const current = ++voiceGeneration;
    try {
      if (voiceKey !== key || !voice) {
        status('Preparing a pronunciation reference…'); voiceAbort = new AbortController();
        const response = await request(root.dataset.pronounceUrl, voiceAbort.signal);
        if (!response.headers.get('Content-Type')?.startsWith('audio/')) throw new Error('The pronunciation service did not return playable audio.');
        const blob = await response.blob(); if (current !== voiceGeneration) return;
        if (voiceUrl) URL.revokeObjectURL(voiceUrl); voiceUrl = URL.createObjectURL(blob); voice = new Audio(voiceUrl); voiceKey = key;
        voice.addEventListener('error', () => status('The reference audio could not play. Please retry.', true));
      }
      if (current !== voiceGeneration) return;
      voice.playbackRate = Number(el('speed').value); voice.preservesPitch = true; await voice.play(); status('Playing model pronunciation reference.');
    } catch (error) { if (current === voiceGeneration && error.name !== 'AbortError') status(error.message || 'Audio could not play. Try Listen again.', true); }
  });
  el('stop').addEventListener('click', () => { stopVoice(); status('Pronunciation reference stopped.'); });
  el('speed').addEventListener('change', () => { if (voice) voice.playbackRate = Number(el('speed').value); });
  window.NextChapterAssistance = Object.assign(window.NextChapterAssistance || {}, {openPractice: (selected) => { stopVoice(); window.dispatchEvent(new CustomEvent('nextchapter:practice', {detail: selected})); }});
  el('practice').addEventListener('click', () => { if (reference && allowed) window.NextChapterAssistance.openPractice({...reference}); });
  el('login').hidden = authenticated;
  el('availability').textContent = !story || !paragraphs.length ? 'No selectable story text is available on this page.' : !authenticated ? 'Sign in for Gemini word and pronunciation help.' : !enabled ? 'Gemini language help is unavailable. Reading and listening still work.' : !yes(root.dataset.voiceEnabled) ? 'Text help and reference pronunciation are available. Microphone analysis is currently unavailable.' : 'Choose a passage to explore its meaning and pronunciation.';
  el('explain').disabled = !allowed || !paragraphs.length;
  if (paragraphs.length) populatePassages(paragraphs[0]);
  window.addEventListener('pagehide', () => { explainAbort?.abort(); stopVoice(true); });
})();
