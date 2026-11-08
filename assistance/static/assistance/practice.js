/* Local-first, bounded mono PCM capture. No microphone or upload on page load. */
(() => {
  'use strict';
  const root = document.getElementById('assistance-root');
  const panel = document.getElementById('practice-panel');
  if (!root || !panel) return;
  const get = name => document.getElementById(`practice-${name}`);
  const status = message => { get('status').textContent = message; };
  let reference = null, stream = null, context = null, source = null, processor = null, mute = null;
  let chunks = [], frames = 0, rate = 0, recording = false, blob = null, replayURL = null, referenceURL = null;
  let timer = null, request = null, generation = 0, previousFocus = null, starting = false;
  const enabled = () => root.dataset.authenticated === 'true' && root.dataset.enabled === 'true';
  const voiceEnabled = () => enabled() && root.dataset.voiceEnabled === 'true';
  const secure = () => window.isSecureContext && navigator.mediaDevices && navigator.mediaDevices.getUserMedia && (window.AudioContext || window.webkitAudioContext);
  const csrf = () => root.querySelector('[name=csrfmiddlewaretoken]')?.value || document.cookie.split('; ').find(x => x.startsWith('csrftoken='))?.slice(10) || '';
  const fields = () => Object.fromEntries(['media_id', 'paragraph', 'start', 'end', 'locale', 'explanation_locale'].map(key => [key, reference[key]]));
  function controls() {
    get('record').disabled = !voiceEnabled() || !secure() || recording || starting || Boolean(request);
    get('stop').hidden = !recording;
    get('analyze').disabled = !blob || Boolean(request) || recording || starting;
    get('discard').disabled = !blob && !recording && !starting && !request;
    get('reference').disabled = !enabled() || recording || starting || Boolean(request);
  }
  function stopHardware() {
    recording = false; starting = false;
    clearInterval(timer); timer = null;
    if (processor) { processor.onaudioprocess = null; processor.disconnect(); processor = null; }
    if (source) { source.disconnect(); source = null; }
    if (mute) { mute.disconnect(); mute = null; }
    if (stream) { stream.getTracks().forEach(track => track.stop()); stream = null; }
    if (context) { const old = context; context = null; old.close().catch(() => {}); }
    get('timer').hidden = true;
  }
  function clearAudio(audio, url) {
    audio.pause(); audio.removeAttribute('src'); audio.load();
    if (url) URL.revokeObjectURL(url);
  }
  function clearPersonal() {
    generation++;
    if (request) request.abort(); request = null;
    stopHardware(); chunks = []; frames = 0; blob = null;
    clearAudio(get('replay'), replayURL); replayURL = null;
    clearAudio(get('reference-audio'), referenceURL); referenceURL = null;
    get('results').hidden = true;
    ['transcript', 'match', 'feedback', 'uncertainty'].forEach(name => { get(name).textContent = ''; });
    controls();
  }
  function close() {
    clearPersonal(); reference = null; get('target').textContent = ''; get('languages').textContent = ''; panel.hidden = true;
    if (previousFocus?.isConnected) previousFocus.focus();
  }
  function wav() {
    const buffer = new ArrayBuffer(44 + frames * 2), view = new DataView(buffer);
    const text = (offset, value) => [...value].forEach((char, index) => view.setUint8(offset + index, char.charCodeAt(0)));
    text(0, 'RIFF'); view.setUint32(4, 36 + frames * 2, true); text(8, 'WAVE'); text(12, 'fmt ');
    view.setUint32(16, 16, true); view.setUint16(20, 1, true); view.setUint16(22, 1, true);
    view.setUint32(24, rate, true); view.setUint32(28, rate * 2, true); view.setUint16(32, 2, true); view.setUint16(34, 16, true);
    text(36, 'data'); view.setUint32(40, frames * 2, true);
    let offset = 44;
    chunks.forEach(chunk => chunk.forEach(sample => { const value = Math.max(-1, Math.min(1, sample)); view.setInt16(offset, value < 0 ? value * 32768 : value * 32767, true); offset += 2; }));
    return new Blob([buffer], {type: 'audio/wav'});
  }
  function stop() {
    if (!recording) return;
    stopHardware();
    if (frames) {
      blob = wav(); chunks = []; frames = 0;
      if (blob.size > 5 * 1024 * 1024) { blob = null; status('Recording was too large. Please try a shorter attempt.'); }
      else { replayURL = URL.createObjectURL(blob); get('replay').src = replayURL; status('Recording stopped. Replay it locally, discard it, or choose Analyze to upload.'); }
    } else status('No audio was captured. Check your microphone and try again.');
    controls();
  }
  async function record() {
    if (!voiceEnabled() || !secure() || starting || recording || request) return;
    clearPersonal(); const token = generation; starting = true; controls();
    // Reference playback must not become part of a pronunciation attempt.
    document.querySelectorAll('audio,video').forEach(media => media.pause());
    status('Requesting microphone permission. Recording starts only if you allow it.');
    try {
      const acquired = await navigator.mediaDevices.getUserMedia({audio: {channelCount: 1, echoCancellation: true, noiseSuppression: true}, video: false});
      if (token !== generation || panel.hidden) { acquired.getTracks().forEach(track => track.stop()); return; }
      stream = acquired;
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      context = new AudioContextClass();
      await context.resume();
      if (token !== generation) return;
      rate = context.sampleRate;
      // Bound every actual capture rate, rather than trusting a requested sample rate.
      if (!Number.isFinite(rate) || rate < 8000 || rate > 96000) throw new Error('This microphone sample rate is unsupported. Try another browser or device.');
      source = context.createMediaStreamSource(stream);
      processor = context.createScriptProcessor(4096, 1, 1);
      mute = context.createGain(); mute.gain.value = 0;
      source.connect(processor); processor.connect(mute); mute.connect(context.destination);
      recording = true; starting = false;
      processor.onaudioprocess = event => {
        if (!recording) return;
        const input = event.inputBuffer.getChannelData(0);
        const count = Math.min(input.length, Math.floor(rate * 15) - frames);
        if (count > 0) { chunks.push(new Float32Array(input.subarray(0, count))); frames += count; }
        if (frames >= rate * 15) stop();
      };
      const started = performance.now();
      get('timer').hidden = false; get('timer').querySelector('span').textContent = '0';
      timer = setInterval(() => {
        const seconds = Math.min(15, Math.floor((performance.now() - started) / 1000));
        get('timer').querySelector('span').textContent = String(seconds);
        if (performance.now() - started >= 15000) stop();
      }, 200);
      status('Recording locally. Other playback is paused. Stop within 15 seconds.'); controls();
    } catch (error) {
      if (token !== generation) return;
      stopHardware(); chunks = []; frames = 0;
      status(error.name === 'NotAllowedError' ? 'Microphone permission was denied. You can still listen to the reference; allow microphone access in your browser to try again.' : error.name === 'NotFoundError' ? 'No microphone was found. Connect one and try again, or listen to the reference.' : error.message || 'Recording is unavailable. Try another browser.'); controls();
    }
  }
  async function failure(response) {
    let data; try { data = await response.json(); } catch (_) { /* Non-JSON gateway response. */ }
    return data?.error?.message || `The service could not complete this request (${response.status}). Please try again.`;
  }
  function render(data) {
    get('transcript').textContent = data.transcript || 'No reliable dictation was returned.';
    get('match').textContent = data.reference_match || 'No reliable comparison was returned.';
    const list = get('feedback'); list.replaceChildren();
    if (data.assessment_supported === true && Array.isArray(data.feedback) && data.feedback.length) {
      data.feedback.forEach(item => { const li = document.createElement('li'); li.textContent = [item.observation, item.suggestion].filter(Boolean).join(' — '); list.append(li); });
    } else { const li = document.createElement('li'); li.textContent = 'Pronunciation could not be assessed reliably. Try a short, clear recording in a quieter space.'; list.append(li); }
    get('uncertainty').textContent = data.uncertainty || 'Automated feedback can be mistaken. A matching transcript does not establish perfect pronunciation.';
    get('results').hidden = false;
  }
  async function analyze() {
    if (!blob || request || !voiceEnabled()) return;
    const token = generation, body = new FormData();
    Object.entries(fields()).forEach(([key, value]) => body.append(key, value)); body.append('audio', blob, 'audio.wav');
    request = new AbortController(); controls(); status('Uploading your recording to Gemini for analysis.');
    try {
      const response = await fetch(root.dataset.practiceUrl, {method: 'POST', credentials: 'same-origin', headers: {'X-CSRFToken': csrf()}, body, signal: request.signal});
      if (!response.ok) throw new Error(await failure(response));
      const data = await response.json(); if (token !== generation) return;
      render(data); status('Analysis complete. Review the dictation separately from the pronunciation observations.');
    } catch (error) { if (token === generation && error.name !== 'AbortError') status(error.message || 'Analysis failed. You can replay or retry your recording.'); }
    finally { if (token === generation) { request = null; controls(); } }
  }
  async function listen() {
    if (!enabled() || recording || starting || request) return;
    const token = generation; request = new AbortController(); controls(); status('Preparing reference audio.');
    try {
      const response = await fetch(root.dataset.pronounceUrl, {method: 'POST', credentials: 'same-origin', headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrf()}, body: JSON.stringify(fields()), signal: request.signal});
      if (!response.ok) throw new Error(await failure(response));
      const audio = await response.blob(); if (token !== generation) return;
      clearAudio(get('reference-audio'), referenceURL); referenceURL = URL.createObjectURL(audio); get('reference-audio').src = referenceURL;
      await get('reference-audio').play(); status('Playing the reference.');
    } catch (error) { if (token === generation && error.name !== 'AbortError') status(error.message || 'Reference audio is unavailable.'); }
    finally { if (token === generation) { request = null; controls(); } }
  }
  window.addEventListener('nextchapter:practice', event => {
    const selected = event.detail;
    if (!selected || !selected.selection || !['media_id', 'paragraph', 'start', 'end', 'locale', 'explanation_locale'].every(key => selected[key] !== undefined)) return;
    clearPersonal(); previousFocus = document.activeElement; reference = {...selected}; panel.hidden = false;
    get('target').textContent = selected.selection; get('languages').textContent = `Practice language: ${selected.locale}. Explanation language: ${selected.explanation_locale}.`;
    status(!enabled() ? 'Sign in and enable assistance to use this feature.' : !voiceEnabled() ? 'Voice analysis is unavailable until the configured Gemini voice service is approved. You can still listen to a reference.' : !secure() ? 'Recording needs HTTPS (or localhost) and a browser with microphone and Web Audio support. You can still listen to a reference.' : 'Listen first, then choose Record. Recording is limited to 15 seconds.');
    controls(); get('heading').focus();
  });
  get('record').addEventListener('click', record); get('stop').addEventListener('click', stop);
  get('analyze').addEventListener('click', analyze); get('reference').addEventListener('click', listen);
  get('discard').addEventListener('click', () => { clearPersonal(); status('Recording discarded. Choose Record to try again.'); get('record').focus(); });
  get('cancel').addEventListener('click', close);
  panel.addEventListener('keydown', event => { if (event.key === 'Escape') { event.preventDefault(); close(); } });
  window.addEventListener('pagehide', clearPersonal);
  window.addEventListener('nextchapter:logout', close);
  document.addEventListener('submit', event => { if (event.target.action && /\/logout\/?(?:\?|$)/.test(event.target.action)) close(); });
  new MutationObserver(() => { if (root.dataset.authenticated !== 'true' || root.hidden || panel.hidden) { clearPersonal(); if (root.dataset.authenticated !== 'true') { reference = null; get('target').textContent = ''; } } }).observe(root, {attributes: true, attributeFilter: ['data-authenticated', 'hidden'], subtree: false});
  new MutationObserver(() => { if (panel.hidden) clearPersonal(); }).observe(panel, {attributes: true, attributeFilter: ['hidden']});
  controls();
})();
