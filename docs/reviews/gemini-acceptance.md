# Gemini integration evidence — November 7, 2026 EST

Feature parent #60; backend #61; panel #62; recorder #63; integration #64.
Integration branch `work/issue-64-f3955c49` incorporates core `run48/integration`
at `67ca4b8` (PR #65). No main merge/deployment/submission is performed.

## Live provider and browser receipts

Owner supplied the backend key in Doppler `hack-coms-hackathon/dev`, authenticated
the CLI, and explicitly confirmed that actual service/data-use configuration
permits personal voice inputs for the 18+ app. Only model IDs and feature flags
were set; no billing/account plan changes. Secrets were read in memory without
printing values or writing credential files. Unrelated Doppler secrets were not
injected into tests, and all test databases were local/temporary SQLite.

- Authenticated model listing advertises generateContent for the selected models.
- `gemini-3.8-flash`: French moi returns /mwa/ and contextual meaning. French maison
  and Spanish libro examples return contextual meanings and IPA.
- `gemini-3.8-flash-tts`: real mono WAV, 24 kHz; corrected moi reference lasts 1.2 s.
  Initial prose instructions were being spoken; production now sends only the
  selected published text and puts language in `speechConfig.languageCode`.
  Public reference dictation returned Moi after the correction.
- `gemini-3.8-flash` audio input accepts generated public speech and returns the
  distinct dictation/reference comparison/feedback/uncertainty schema.
- `scripts.check_assistance_live` passed in headless Edge: explanation -> real
  playable reference -> browser capture from generated public French speech ->
  Stop -> local replay -> explicit Analyze -> actual Gemini result -> Discard.
  App receipts: `/assist/explain/` 200, `/assist/pronounce/` 200,
  `/assist/practice/` 200. No route/provider mocks in this smoke.

Generated speech through synthetic microphone input proves transport/UI wiring,
not human pronunciation assessment or microphone behavior on a physical device.
No personal audio/transcripts were committed or saved as practice history.

## Reproducible local checks

`python manage.py test` includes provider/schema/CSRF/auth/privacy/quota/cache/WAV
and full core catalog/reader/clubs/progress/report regressions. Windows lacks
symlink privileges here; only WinError 1314 skips the two symlink cases. Linux CI
still runs both. Run results and exact reviewed commit are recorded in the PR.

`python manage.py test scripts.check_assistance_browser` passes against actual
Edge, temporary Django DB, fixture provider and synthetic microphone. It covers
Unicode codepoint offsets after an emoji, safe text rendering, 320/390 px layout,
keyboard picker/Escape, playable WAV, playback control, quota error, microphone
permission refusal, no upload before Analyze, PCM WAV duration/container, local
replay, duplicate Analyze prevention while pending, 15-second automatic stop,
discard/close track cleanup and missing-key 503 from the real backend.
Screenshots were inspected; test output lives in the OS temp directory and contains
only public synthetic fixtures. Automated viewport checks do not substitute for
screen-reader or physical mobile-device testing.

Two Windows integration fixes preserve startup: `.gitattributes` prevents CRLF
conversion of hash-addressed bundled text, and test skips are restricted to the
OS's missing-symlink-privilege error. No resource hashes/content were weakened.
`seed_demo` twice and `verify_demo` validate 12 media items and four clubs; static
collection includes both core and assistance assets.

## Remaining acceptance boundary

An independently annotated human pronunciation benchmark remains open in #64/#60.
It must include correct, wrong-word, silent/noisy and accent-varied attempts, plus
same-transcript/different-articulation pairs. Human/reference annotations must
precede model grading. Record errors detected, missed and unable to assess; keep
recordings consented/local and publish no private transcripts. Model self-reports
and synthetic reference matching do not pass this criterion. No calibrated score,
phoneme confidence, learning improvement or reliable error-detection rate is claimed.

Production also requires optional Redis dependency installation, shared-cache
connectivity, backend secrets/flags, permitted provider configuration, HTTPS and
actual deployment verification. Default local LocMem quotas are per process;
production assistance fails closed without an atomic shared backend. The core
library remains usable without Gemini. Mobile Safari/Web Audio and a real human
microphone still require manual rehearsal before judging.
