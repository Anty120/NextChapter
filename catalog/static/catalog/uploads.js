(() => {
  'use strict';
  const form = document.querySelector('[data-upload-form]');
  if (!form) return;
  const input = form.querySelector('[type=file]'), button = form.querySelector('[type=submit]');
  const status = form.querySelector('[data-upload-status]');
  input.addEventListener('change', () => {
    const file = input.files[0]; input.setCustomValidity(''); status.textContent='';
    if (!file) return;
    if (file.size > 3*1024*1024 || !file.size) input.setCustomValidity('Choose a nonempty PDF or MP3 of up to 3 MiB.');
    else if (!/\.(pdf|mp3)$/i.test(file.name)) input.setCustomValidity('Choose a PDF book or MP3 song.');
    else {
      status.textContent = `${file.name} · ${(file.size/1024/1024).toFixed(2)} MiB · ready to upload.`;
      const title = form.querySelector('[name=title]');
      if (!title.value.trim()) title.value=file.name.replace(/\.(pdf|mp3)$/i,'').slice(0,180);
    }
  });
  form.addEventListener('submit', () => {
    button.disabled=true;button.setAttribute('aria-busy','true');status.textContent='Uploading and checking your file…';
  });
  window.addEventListener('pageshow', () => {button.disabled=false;button.removeAttribute('aria-busy');});
})();
