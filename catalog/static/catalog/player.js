/* Native playback stays usable without JavaScript. Personal progress is server-backed. */
(() => {
  const player = document.getElementById('player');
  const form = document.getElementById('audio-progress');
  const error = document.getElementById('audio-error');
  if (!player) return;
  player.addEventListener('error', () => { error.hidden = false; });
  player.querySelector('source')?.addEventListener('error', () => { error.hidden = false; });
  const speed = document.getElementById('playback-speed');
  speed?.addEventListener('change', () => { player.playbackRate = Number(speed.value); });
  const saved = Number(player.dataset.seconds);
  let restoring = true;
  function restorePosition() {
    if (Number.isFinite(saved) && saved > 0 && saved <= player.duration) {
      // Ignore the zero-time events emitted while native metadata/seek settles.
      player.addEventListener('seeked', () => { restoring = false; }, { once: true });
      player.currentTime = saved;
    } else {
      restoring = false;
    }
  }
  // Cached audio can load its metadata before this deferred script runs (#40).
  if (player.readyState >= 1) restorePosition();
  else player.addEventListener('loadedmetadata', restorePosition, { once: true });
  if (!form) return;
  const input = document.getElementById('audio-seconds');
  const status = document.getElementById('save-status');
  let lastSaved = Number.isFinite(saved) ? saved : -1;
  let pending = false;
  let queued = false;
  async function save() {
    if (restoring || player.seeking || player.readyState < 1) return;
    if (pending) { queued = true; return; }
    if (!Number.isFinite(player.currentTime) || player.currentTime === lastSaved) return;
    const position = player.currentTime;
    input.value = position.toFixed(1);
    const body = new FormData(form);
    pending = true;
    status.textContent = 'Saving your listening position…';
    try {
      const response = await fetch(form.action, {
        method: 'POST', body, credentials: 'same-origin', keepalive: true,
        headers: { Accept: 'application/json' },
      });
      if (!response.ok || !(response.headers.get('content-type') || '').includes('application/json')) throw new Error('Save failed');
      lastSaved = position;
      status.textContent = 'Your listening position is saved.';
      // Lets the optional listening deck move its saved-position marker.
      player.dispatchEvent(new CustomEvent('progress-saved', { detail: { seconds: position } }));
    } catch {
      status.textContent = 'Could not save your place. Check your connection or sign in again, then use Save listening position.';
    } finally {
      pending = false;
      if (queued) { queued = false; save(); }
    }
  }
  player.addEventListener('timeupdate', () => {
    if (restoring || player.seeking) return;
    input.value = player.currentTime.toFixed(1);
    if (Math.abs(player.currentTime - lastSaved) >= 5) save();
  });
  player.addEventListener('pause', save);
  player.addEventListener('seeked', save);
  player.addEventListener('ended', save);
  document.addEventListener('visibilitychange', () => { if (document.hidden) save(); });
  window.addEventListener('pagehide', save);
})();
