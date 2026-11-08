/* Custom listening deck layered over the native <audio id="player">.
   The native element stays focusable and authoritative (reader.css hides its strip
   visually while the deck is up, and keyboard focus brings it back): the deck only
   calls play()/pause()/currentTime on it and mirrors its events. player.js still
   owns resume and saving, so this file can fail without losing anyone's place. */
(() => {
  const audio = document.getElementById('player');
  const deck = document.querySelector('[data-deck]');
  if (!audio || !deck) return;
  const M = window.Motion;
  const UI = window.NextChapterUI;
  const reduced = () => (UI ? UI.reduced() : window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  const play = deck.querySelector('[data-deck-play]');
  const seek = deck.querySelector('[data-deck-seek]');
  const fill = deck.querySelector('.deck-fill');
  const saved = deck.querySelector('.deck-saved');
  const currentText = deck.querySelector('[data-deck-current]');
  const durationText = deck.querySelector('[data-deck-duration]');
  const iconPlay = deck.querySelector('.deck-icon-play');
  const iconPause = deck.querySelector('.deck-icon-pause');
  deck.hidden = false;
  // If the recording cannot load, step aside: the native player and its error message remain.
  const stepAside = () => { deck.hidden = true; };
  audio.addEventListener('error', stepAside);
  audio.querySelector('source')?.addEventListener('error', stepAside);
  if (audio.error) stepAside();

  const clock = (s) => {
    if (!Number.isFinite(s) || s < 0) return '–:––';
    const m = Math.floor(s / 60);
    return `${m}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
  };
  const duration = () => (Number.isFinite(audio.duration) && audio.duration > 0 ? audio.duration : 0);
  let scrubbing = false;

  // Per frame, only a transform is written. Text and the slider value change layout,
  // so they are written only when the visible second changes.
  let shownSecond = -1;
  function render(time = audio.currentTime) {
    const d = duration();
    const p = d ? Math.min(1, Math.max(0, time / d)) : 0;
    fill.style.transform = `scaleX(${p})`;
    const second = Math.floor(time);
    if (second === shownSecond) return;
    shownSecond = second;
    currentText.textContent = clock(time);
    if (!scrubbing && d) seek.value = String(time);
  }
  function setDuration() {
    const d = duration();
    if (!d) return;
    seek.max = String(d);
    durationText.textContent = clock(d);
    placeSaved(Number(audio.dataset.seconds), false);
    render();
  }

  /* Where you last saved: a tick on the track. After each save it springs to the new
     spot, so saving is visible where you are looking, not only in a status line. */
  function placeSaved(seconds, animate) {
    const d = duration();
    if (!saved || !d || !Number.isFinite(seconds) || seconds <= 0) { if (saved) saved.hidden = true; return; }
    saved.hidden = false;
    const target = `translateX(${(Math.min(seconds, d) / d) * 100}%)`;
    if (animate && M && !reduced()) M.animate(saved, { transform: target }, UI.SPRING.slap);
    else saved.style.transform = target;
  }
  audio.addEventListener('progress-saved', (event) => placeSaved(event.detail.seconds, true));

  /* Play/pause icon morph: the two glyphs cross-fade through a small blur and scale,
     so they read as one control changing state rather than two icons swapping. */
  function reflect() {
    const playing = !audio.paused && !audio.ended;
    deck.dataset.state = playing ? 'playing' : 'paused';
    play.setAttribute('aria-label', playing ? 'Pause' : 'Play');
    if (!M) return;
    const show = playing ? iconPause : iconPlay;
    const hide = playing ? iconPlay : iconPause;
    if (reduced()) {
      M.animate(show, { opacity: 1, transform: 'none' }, { duration: 0.12 });
      M.animate(hide, { opacity: 0 }, { duration: 0.12 });
      return;
    }
    UI.clearFilter(M.animate(show, { opacity: 1, transform: 'scale(1) rotate(0deg)', filter: 'blur(0px)' }, { ...UI.SPRING.slap, opacity: { duration: 0.16 }, filter: { duration: 0.16 } }), show);
    M.animate(hide, { opacity: 0, transform: `scale(.6) rotate(${playing ? -30 : 30}deg)`, filter: 'blur(3px)' }, UI.QUICK);
  }

  // While playing, a rAF loop reads currentTime and writes one transform: no layout.
  let raf = 0;
  const tick = () => { render(); raf = audio.paused ? 0 : requestAnimationFrame(tick); };
  audio.addEventListener('play', () => { reflect(); if (!raf) raf = requestAnimationFrame(tick); });
  audio.addEventListener('pause', reflect);
  audio.addEventListener('ended', reflect);
  audio.addEventListener('timeupdate', () => { if (!raf) render(); });
  audio.addEventListener('seeked', () => render());
  audio.addEventListener('loadedmetadata', setDuration);
  audio.addEventListener('durationchange', setDuration);
  if (audio.readyState >= 1) setDuration();

  // No autoplay ever: playback starts only from this explicit press.
  play.addEventListener('click', () => {
    if (audio.paused || audio.ended) audio.play().catch(() => { /* blocked or failed: native error UI handles it */ });
    else audio.pause();
  });
  deck.querySelectorAll('[data-deck-skip]').forEach((button) => button.addEventListener('click', () => {
    const d = duration();
    if (!d) return;
    audio.currentTime = Math.min(d, Math.max(0, audio.currentTime + Number(button.dataset.deckSkip)));
  }));

  // Volume stays reachable with the native strip hidden; follows native changes too.
  const volume = deck.querySelector('[data-deck-volume]');
  volume?.addEventListener('input', () => { audio.volume = Number(volume.value); audio.muted = audio.volume === 0; });
  audio.addEventListener('volumechange', () => { if (volume) volume.value = String(audio.muted ? 0 : audio.volume); });

  // Scrubbing previews the time; the seek is committed once (on change), so the
  // native element and player.js see a single seek and save once.
  seek.addEventListener('pointerdown', () => { scrubbing = true; });
  seek.addEventListener('input', () => {
    const d = duration();
    if (!d) return;
    const t = Number(seek.value);
    fill.style.transform = `scaleX(${t / d})`;
    currentText.textContent = clock(t);
    shownSecond = -1;
  });
  seek.addEventListener('change', () => {
    scrubbing = false;
    if (duration()) audio.currentTime = Number(seek.value);
  });
  reflect();
  render();
})();
