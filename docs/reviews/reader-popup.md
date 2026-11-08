# Reader popup and local Gemini follow-up

User requested contextual word help instead of the full assistance panel and a
fix in the local main app. Existing #64 was returned Ready and reserved under
claim `7fb443b511b36a7075d29e7b4b8f6592bf8c5925`; source work is isolated in
`work/issue-64-7fb443b5`, based on main `a137acf`.

## Causes and fixes

- The running localhost:8000 page rendered `data-enabled=false`. The ordinary
  runserver process did not inherit the available Doppler Gemini configuration.
  Development runserver now loads missing Gemini settings from the signed-in
  Doppler CLI, preserves explicit environment overrides, and prints safe,
  actionable diagnostics. No shared DATABASE_URL or other secrets are imported.
  Migrations, tests, builds and production WSGI do not auto-fetch credentials.
- Word clicks inside the reading bookmark form were ignored because the event
  handler excluded all form descendants. It now excludes actual interactive
  controls while allowing prose inside a form.
- Word clicks and sentence highlights now open a compact fixed popup anchored
  to the text range. It has Explain, Listen, Copy and optional Practice actions;
  translation/IPA are concise. Detailed sound guidance and the keyboard picker
  are collapsed/hidden until requested. No backdrop, focus trap or reader jump.
  Outside click/Escape dismiss; scrolling/resize repositions the popup within
  the viewport, and leaving the selection behind dismisses it.

## Verification

- 90 Django tests pass on Windows; only the two previously documented symlink
  privilege cases skip. The startup tests verify development-only operation,
  scoped injection, preserved overrides and sanitized authentication failures.
- Real Edge browser rehearsal passes with a fixture provider and synthetic mic:
  actual word click inside the bookmark form, Unicode offsets, no selection
  scroll jump, compact card bounds, Copy, 320/390/1024 widths, outside/Escape,
  keyboard picker, safe rendering, voice controls, error/retry and the full
  local-record/replay/explicit-upload/discard/logout workflow.
- Scoped startup loading was exercised against the actual signed-in Doppler
  config: enabled/voice-enabled true, key/models present, database not imported.
- The opt-in live browser smoke passes with actual Gemini: explanation,
  generated speech, and audio analysis all return 200. The microphone input is
  generated public French speech, not a learner's personal recording. Existing
  pronunciation-quality benchmark and physical-device limits remain open.
- JavaScript syntax, Django checks and whitespace checks pass. Final exact-head
  CI and actual main runtime receipts are recorded on the PR/issue.

Only public synthetic fixtures appear in the screenshots. No API keys, real
practice recordings or personal transcripts are committed.
