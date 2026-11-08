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
  let anchorRange = null, anchorElement = null;
  const lookupCache = new Map(), hints = new Map();
  const coach = document.createElement('section'); coach.className = 'sentence-coach'; coach.setAttribute('aria-label', 'Sentence learning tools');
  const points = (s) => Array.from(s);
  const prefixLength = (text, offset) => points(text.slice(0, offset)).length;
  const locale = story?.dataset.assistLocale || root.dataset.targetLocale || 'en-US';
  const status = (message, error = false) => { el('status').textContent = message; el('status').classList.toggle('assist-error', error); };
  function position() {
    if (panel.hidden) return;
    const rect = anchorRange?.getBoundingClientRect() || (anchorElement || el('open')).getBoundingClientRect();
    const width = document.documentElement.clientWidth, height = window.innerHeight, gap = 10, edge = 12;
    panel.style.maxHeight = `${Math.min(480, height - edge * 2)}px`;
    const box = panel.getBoundingClientRect();
    const left = Math.max(edge, Math.min(rect.left + rect.width / 2 - box.width / 2, width - box.width - edge));
    const above = rect.top - box.height - gap;
    const top = above >= edge ? above : Math.min(height - box.height - edge, rect.bottom + gap);
    panel.style.left = `${left}px`; panel.style.top = `${Math.max(edge, top)}px`;
  }
  function rangeFor(p, start, end) {
    const range = document.createRange(), walker = document.createTreeWalker(p.prose, NodeFilter.SHOW_TEXT);
    const from = points(p.prose.textContent).slice(0, start).join('').length;
    const to = points(p.prose.textContent).slice(0, end).join('').length;
    let offset = 0, began = false, node;
    while ((node = walker.nextNode())) {
      if (!began && from <= offset + node.length) { range.setStart(node, from - offset); began = true; }
      if (began && to <= offset + node.length) { range.setEnd(node, to - offset); return range; }
      offset += node.length;
    }
    return null;
  }
  const stopVoice = (dispose = false) => {
    voiceAbort?.abort(); voiceAbort = null; voiceGeneration++;
    if (voice) { voice.pause(); voice.currentTime = 0; }
    el('stop').hidden = true;
    if (dispose) { voice = null; if (voiceUrl) URL.revokeObjectURL(voiceUrl); voiceUrl = null; voiceKey = ''; }
  };
  const show = (moveFocus = true) => {
    if (panel.hidden) opener = document.activeElement;
    panel.hidden = false; el('open').setAttribute('aria-expanded', 'true');
    position();
    if (moveFocus) el('title').focus({preventScroll: true});
  };
  const close = (restoreFocus = false) => {
    explainAbort?.abort(); generation++; stopVoice(); el('explain').removeAttribute('aria-busy');
    const practice = root.querySelector('#practice-panel'); if (practice) practice.hidden = true;
    panel.hidden = true; el('open').setAttribute('aria-expanded', 'false');
    CSS.highlights?.delete('reader-word');
    if (restoreFocus && opener instanceof HTMLElement && opener.isConnected && opener !== document.body) opener.focus({preventScroll: true});
  };
  const csrf = () => root.querySelector('[name=csrfmiddlewaretoken]')?.value || document.cookie.split('; ').find((v) => v.startsWith('csrftoken='))?.slice(10) || '';
  const payload = () => reference && ({media_id: reference.media_id, paragraph: reference.paragraph, start: reference.start, end: reference.end, locale: reference.locale, explanation_locale: reference.explanation_locale});
  const errors = {401: 'Please log in again to use language help.', 403: 'Your session could not be verified. Refresh this page and retry.', 429: 'Language help is busy. Wait a moment, then retry.', 503: 'Language help is not configured or temporarily unavailable. You can continue reading.', 502: 'The language service could not finish. Please retry.'};
  const request = async (url, signal, data = payload()) => {
    if (!url) throw new Error('Language help is not configured. You can continue reading.');
    const response = await fetch(url, {method: 'POST', credentials: 'same-origin', headers: {'Content-Type': 'application/json', 'X-CSRFToken': decodeURIComponent(csrf()), Accept: 'application/json, audio/*'}, body: JSON.stringify(data), signal});
    if (!response.ok) {
      let data; try { data = await response.json(); } catch (_) { /* Status fallback remains useful. */ }
      throw new Error(data?.error?.message || errors[response.status] || 'That passage could not be explained. Choose a shorter passage or retry.');
    }
    return response;
  };
  function choose(p, start, end, moveFocus = false, limit = 300) {
    const practice = root.querySelector('#practice-panel'); if (practice) practice.hidden = true;
    const text = p.prose.textContent;
    if (start < 0 || end <= start || end > points(text).length || end - start > limit) {
      explainAbort?.abort(); generation++; stopVoice(true); reference = null;
      el('result').hidden = true; el('actions').hidden = true; el('explain').disabled = true;
      show(moveFocus); status('Choose a word or sentence of at most 300 characters.', true); return false;
    }
    explainAbort?.abort(); generation++; stopVoice(true);
    reference = {media_id: Number(story.dataset.assistMedia || root.dataset.mediaId), paragraph: p.index, start, end, locale, explanation_locale: root.dataset.explanationLocale || 'en', selection: points(text).slice(start, end).join('')};
    showCoach(p, start);
    anchorRange = rangeFor(p, start, end); anchorElement = p.prose;
    if (anchorRange && typeof Highlight === 'function' && CSS.highlights) CSS.highlights.set('reader-word', new Highlight(anchorRange));
    el('selection').textContent = reference.selection; el('selection').lang = locale;
    el('copy').disabled = false; el('details').open = false;
    el('result').hidden = true; el('actions').hidden = !allowed;
    el('paragraph').value = String(p.index); populatePassages(p, start, end);
    el('explain').disabled = !allowed; el('explain').removeAttribute('aria-busy');
    status(''); show(moveFocus); return true;
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
  async function explain(full = false) {
    if (!reference || !allowed) return;
    explainAbort?.abort(); explainAbort = new AbortController(); const current = ++generation;
    const url = full ? root.dataset.explainUrl : reference.end - reference.start > 300 ? root.dataset.sentenceUrl : root.dataset.lookupUrl || root.dataset.explainUrl;
    const key = url + JSON.stringify(payload()), cached = lookupCache.get(key);
    status(cached ? '' : 'Looking up…'); el('result').hidden = true; el('explain').setAttribute('aria-busy', 'true');
    try {
      const data = cached || await (await request(url, explainAbort.signal)).json();
      if (current !== generation) return;
      if (!cached) { lookupCache.set(key, data); if (lookupCache.size > 256) lookupCache.delete(lookupCache.keys().next().value); }
      const meaning = typeof data.translation === 'string' && data.translation.trim() ? data.translation : data.meaning;
      el('meaning').textContent = typeof meaning === 'string' ? (points(meaning).length > 220 ? points(meaning).slice(0, 220).join('') + '…' : meaning) : '';
      el('ipa').textContent = typeof data.ipa === 'string' ? data.ipa : '';
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
      el('result').hidden = false; status(''); position();
    } catch (error) { if (current === generation && error.name !== 'AbortError') status(navigator.onLine === false ? 'You are offline. Reconnect and choose Explain selection to retry.' : error.message, true); }
    finally { if (current === generation) el('explain').removeAttribute('aria-busy'); }
  }
  function captureSelection(moveFocus = false) {
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
  el('open').addEventListener('click', () => {
    if (!captureSelection(false) && !reference && paragraphs.length) el('passage').dispatchEvent(new Event('change'));
    anchorRange = null; anchorElement = el('open'); el('picker').hidden = false; el('picker').open = true; show(true);
  });
  el('close').addEventListener('click', () => close(true));
  document.addEventListener('keydown', (event) => { if (event.key === 'Escape' && !panel.hidden) { event.preventDefault(); close(true); } });
  document.addEventListener('pointerdown', (event) => { if (!panel.hidden && !root.contains(event.target) && !story?.contains(event.target)) close(); });
  el('copy').addEventListener('click', async () => {
    if (!reference) return;
    try { await navigator.clipboard.writeText(reference.selection); status('Copied.'); }
    catch (_) { status('Copy is unavailable. Select the text and use your device’s Copy command.', true); }
  });
  el('explain').addEventListener('click', () => { captureSelection(false); explain(); });
  el('deeper').addEventListener('click', () => explain(true));
  for (const p of paragraphs) { const option = document.createElement('option'); option.value = String(p.index); option.textContent = `Paragraph ${p.index + 1}: ${p.prose.textContent.slice(0, 65)}`; el('paragraph').append(option); }
  el('paragraph').addEventListener('change', () => { window.getSelection()?.removeAllRanges(); const p = paragraphs.find((p) => String(p.index) === el('paragraph').value); populatePassages(p); el('passage').dispatchEvent(new Event('change')); });
  el('passage').addEventListener('change', () => { window.getSelection()?.removeAllRanges(); const p = paragraphs.find((p) => String(p.index) === el('paragraph').value); const [start, end] = el('passage').value.split(':').map(Number); if (p) choose(p, start, end, false); });
  story?.addEventListener('pointerup', () => {
    if (window.getSelection()?.toString().trim() && captureSelection(false)) { el('picker').open = false; el('picker').hidden = true; position(); }
  });
  story?.addEventListener('keyup', (event) => { if (event.key === 'Shift') captureSelection(false); });
  story?.addEventListener('click', (event) => {
    if (event.target.closest('a,button,input,select,textarea,label') || window.getSelection()?.toString().trim()) return;
    const p = paragraphs.find((p) => p.prose.contains(event.target)); if (!p) return;
    let node, offset;
    if (document.caretPositionFromPoint) { const caret = document.caretPositionFromPoint(event.clientX, event.clientY); node = caret?.offsetNode; offset = caret?.offset; }
    else if (document.caretRangeFromPoint) { const caret = document.caretRangeFromPoint(event.clientX, event.clientY); node = caret?.startContainer; offset = caret?.startOffset; }
    if (!node || !p.prose.contains(node)) return;
    const before = document.createRange(); before.selectNodeContents(p.prose); before.setEnd(node, offset); const at = points(before.toString()).length;
    const word = segments(p.prose.textContent, 'word').find((s) => at >= s.start && at < s.end);
    if (word && choose(p, word.start, word.end)) { el('picker').open = false; el('picker').hidden = true; position(); explain(); }
  });
  el('listen').addEventListener('click', async () => {
    if (!reference || !allowed) return;
    window.dispatchEvent(new CustomEvent('nextchapter:reference-playback', {detail: {owner: 'panel'}}));
    document.querySelectorAll('audio,video').forEach(media => media.pause());
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
      voice.playbackRate = Number(el('speed').value); voice.preservesPitch = true; await voice.play(); el('stop').hidden = false; status('Playing pronunciation.');
      voice.onended = () => { el('stop').hidden = true; status(''); };
    } catch (error) { if (current === voiceGeneration && error.name !== 'AbortError') status(error.message || 'Audio could not play. Try Listen again.', true); }
  });
  el('stop').addEventListener('click', () => { stopVoice(); status('Pronunciation reference stopped.'); });
  el('speed').addEventListener('change', () => { if (voice) voice.playbackRate = Number(el('speed').value); });
  window.addEventListener('nextchapter:reference-playback', (event) => {
    if (event.detail?.owner !== 'panel') stopVoice();
  });
  document.addEventListener('play', (event) => {
    if (!(event.target instanceof HTMLMediaElement)) return;
    window.dispatchEvent(new CustomEvent('nextchapter:reference-playback', {
      detail: {owner: event.target.id === 'practice-reference-audio' ? 'practice' : 'media'}
    }));
    stopVoice();
    document.querySelectorAll('audio,video').forEach(media => { if (media !== event.target) media.pause(); });
  }, true);
  window.addEventListener('nextchapter:recording', (event) => {
    if (event.detail?.active) stopVoice();
    el('listen').disabled = Boolean(event.detail?.active);
    el('practice').disabled = Boolean(event.detail?.active);
  });
  window.NextChapterAssistance = Object.assign(window.NextChapterAssistance || {}, {openPractice: (selected) => { stopVoice(); el('details').open = false; el('picker').open = false; el('picker').hidden = true; window.dispatchEvent(new CustomEvent('nextchapter:practice', {detail: selected})); }});
  el('practice').addEventListener('click', () => { if (reference && allowed) practiceSentence(reference); });
  el('login').hidden = authenticated;
  el('availability').textContent = !story || !paragraphs.length ? 'No readable text here.' : !authenticated ? '' : !enabled ? 'Word help is temporarily unavailable.' : '';
  el('explain').disabled = !allowed || !paragraphs.length;
  if (paragraphs.length) populatePassages(paragraphs[0]);
  function sentenceAt(p, at) {
    return segments(p.prose.textContent, 'sentence').find(s => at >= s.start && at < s.end)
      || segments(p.prose.textContent, 'sentence')[0];
  }
  function practiceSentence(selected) {
    const p = paragraphs.find(p => p.index === selected.paragraph), sentence = p && sentenceAt(p, selected.start);
    if (!sentence || !choose(p, sentence.start, sentence.end, false, 1500)) return;
    window.NextChapterAssistance.openPractice({...reference});
  }
  function showCoach(p, at) {
    const sentence = sentenceAt(p, at); if (!sentence) return;
    coach.replaceChildren();
    const label = document.createElement('strong'); label.textContent = 'Try the whole sentence';
    const quote = document.createElement('div'); quote.className = 'sentence-quote'; quote.textContent = sentence.text.trim(); quote.lang = locale;
    const actions = document.createElement('div'); actions.className = 'sentence-buttons';
    const add = (text, action) => { const b = document.createElement('button'); b.type = 'button'; b.textContent = text; b.disabled = !allowed; b.addEventListener('click', action); actions.append(b); return b; };
    const selected = {media_id: Number(root.dataset.mediaId), paragraph:p.index, start:sentence.start, end:sentence.end,
      locale, explanation_locale:root.dataset.explanationLocale || 'en', selection:sentence.text};
    add('🎙 Speak sentence', () => practiceSentence(selected));
    add('Explain sentence', () => { if (choose(p, sentence.start, sentence.end, false, 1500)) explain(); });
    const hintButton = add('Pronunciation hints', async () => {
      const key = `${p.index}:${sentence.start}:${sentence.end}`;
      if (hints.has(key)) { hints.delete(key); renderHints(p); hintButton.textContent = 'Pronunciation hints'; return; }
      hintButton.disabled = true; hintButton.textContent = 'Preparing hints…';
      try {
        const data = await (await request(root.dataset.phoneticsUrl, undefined, selected)).json();
        hints.set(key, {paragraph:p.index, start:sentence.start, words:data.words}); renderHints(p);
        hintButton.textContent = 'Hide hints';
      } catch (error) { hintButton.textContent = 'Retry hints'; coach.querySelector('.sentence-note').textContent = error.message; }
      finally { hintButton.disabled = !allowed; }
    });
    const note = document.createElement('small'); note.className = 'sentence-note'; note.textContent = 'Sound hints are approximate; listen to the reference too. Up to 60 seconds per attempt.';
    coach.append(label, quote, actions, note); p.prose.after(coach);
  }
  function renderHints(p) {
    const text = points(p.prose.textContent), fragment = document.createDocumentFragment(); let cursor = 0;
    const words = Array.from(hints.values()).filter(h => h.paragraph === p.index)
      .flatMap(h => h.words.map(w => ({...w,start:w.start+h.start,end:w.end+h.start}))).sort((a,b) => a.start-b.start);
    for (const word of words) {
      if (word.start < cursor || text.slice(word.start,word.end).join('') !== word.text) continue;
      fragment.append(document.createTextNode(text.slice(cursor,word.start).join('')));
      const span = document.createElement('span'); span.className = 'phonetic-word'; span.textContent = word.text;
      span.dataset.sound = word.sound || word.ipa; span.title = `${word.ipa} · approximate: ${word.sound}`;
      fragment.append(span); cursor = word.end;
    }
    fragment.append(document.createTextNode(text.slice(cursor).join(''))); p.prose.replaceChildren(fragment);
    if (reference?.paragraph === p.index) { anchorRange = rangeFor(p,reference.start,reference.end); if (anchorRange && typeof Highlight === 'function' && CSS.highlights) CSS.highlights.set('reader-word',new Highlight(anchorRange)); position(); }
  }
  if (paragraphs.length) showCoach(paragraphs.find(p => p.prose.textContent.length >= 30) || paragraphs[0], 0);
  new ResizeObserver(position).observe(panel);
  window.addEventListener('resize', position);
  window.addEventListener('scroll', (event) => {
    if (panel.hidden || panel.contains(event.target)) return;
    const rect = anchorRange?.getBoundingClientRect();
    if (rect && (rect.bottom < 0 || rect.top > window.innerHeight)) close(); else position();
  }, true);
  window.addEventListener('pagehide', () => { explainAbort?.abort(); stopVoice(true); });
})();
