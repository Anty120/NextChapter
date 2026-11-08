# Gemini reader and speech assistance

Implementation tracks #60–#64. This is optional, user-requested language help,
including voluntary pronunciation practice. It does not lock content or change
any member's proficiency level. The Django media library works without Gemini.

## Run

Use the application's normal virtual environment, migrations, seed command and
server. The new assistance app requires no migrations or additional packages.
For local `python manage.py runserver`, startup loads missing Gemini settings
from the signed-in Doppler CLI (`hack-coms-hackathon/dev`). The CLI must be on
PATH or at `.venv/doppler/doppler[.exe]`. Existing process settings take precedence;
`GEMINI_ENABLED=false` explicitly keeps assistance off. `DOPPLER_PROJECT` and
`DOPPLER_CONFIG` select a different authorized development config when needed.
Only Gemini settings are imported: shared database URLs and other secrets are
never pulled into local startup. No credentials are written to a project file.
Restart an already-running server after configuration changes. Failed local
loading prints an actionable startup diagnostic without secret/provider output.
This bootstrap runs only for development runserver; migrations, seeding, tests,
production WSGI and builds do not contact Doppler automatically.
On a published story/book or a transcript/lyrics page, sign in, click a word or
select a sentence. A compact popup opens next to the selection, with Explain,
Listen and Copy. Clicking a word explains it immediately; highlighted sentences
wait for Explain. Short translation/IPA appear inline, with pronunciation details
and voluntary practice expanded only on request. Outside click/Escape dismiss
the popup without scrolling the reader. Keyboard and touch users can open Word
help and use its passage picker. Reference speech plays only on request.

The reader shows contextual meaning, translation, IPA when available, sound
guidance and nearby sound examples. English mnemonics are approximations: French
`moi` /mwa/ includes /wa/, roughly “wah”; comparisons with “water” vary with the
English speaker's accent.

## Backend configuration

Inject these through the backend environment or the team's approved Doppler
configuration. Never copy a key to a browser/Vite variable or commit it. The app
does **not** load `.env.example` automatically.

```text
GEMINI_ENABLED=true
GEMINI_API_KEY=<injected backend secret>
GEMINI_TEXT_MODEL=<current generateContent-compatible text model>
GEMINI_TTS_MODEL=<current generateContent-compatible speech model>
GEMINI_AUDIO_MODEL=<current generateContent-compatible audio-input model>
```

Model identifiers have no hardcoded defaults. Verify current availability and
transport compatibility for the actual project; a documentation example alone
does not prove that a model is enabled for an account. The implementation uses
the standard-library REST transport so existing dependency locks stay unchanged.

Voice submission is separately disabled by default:

```text
GEMINI_VOICE_INPUT_ENABLED=true
GEMINI_VOICE_INPUT_APPROVED=true
```

Set the approval flag only after the owner verifies that the configured provider
service/data-use policy permits personal voice inputs for the intended users
and regions. The flag records that configuration decision; it is not a substitute
for doing the check or permission to activate billing. The existing 18+ hackathon
decision is retained. No billing/account changes are performed by this code.

Timeout, per-user request rate and reference-cache TTL are configurable
with the `GEMINI_*` variables in `.env.example`. Production needs a shared cache
backend suitable for rate/concurrency limits across processes; a process-local
cache cannot enforce a global serverless request budget. Missing configuration,
unavailable models, quota and network failures produce explicit errors. Each user
can have one in-flight request. A zero cache TTL disables reference caching.

For production, install `python -m pip install --require-hashes -r requirements-assistance.txt`
in addition to the main requirements and inject `GEMINI_CACHE_URL` with the
owner's Redis connection URL (prefer `rediss://`). The setting selects Django's
built-in Redis cache with bounded connection/read timeouts. Redis is optional for
single-process local development. Production assistance returns 503 without a
shared cache; core reading/community continue to work. Add the optional install
to the deployment build before enabling assistance there. Do not expose the URL
or credentials in the browser. Shared Redis connectivity is a deployment check.

## Recording flow

Practice starts from a selected reference. Listen first, then choose Record.
The browser asks for microphone permission only after that action. Stop creates
a mono PCM WAV in browser memory; Listen to my attempt lets you replay it locally.
Discard/Close releases the recording. Analyze is the explicit upload action.
Recordings are limited to 15 seconds and 5 MiB, with matching server-side checks.
Microphone capture requires HTTPS or localhost and a supported Web Audio browser.

No browser recognizer is silently used instead of Gemini. The server receives
the actual recording, the reference resolved from published media, and an explicit
language/locale. It returns dictation separately from sound observations and
uncertainty. Neither matching words nor the LLM's opinion establishes a calibrated
pronunciation score. Unreliable analysis must return unable-to-assess. This is
qualitative assistance, not a certified assessment or automatic grading system.

The app does not store practice audio/transcripts as history or put them in logs.
Reference text/audio caching excludes personal attempts. Provider retention follows
the actual service terms; the app does not promise that the provider retains
nothing. Closing/canceling releases microphone tracks and local audio URLs.

## Verification and limits

Backend tests use a mocked provider to cover canonical selection offsets,
authorization/CSRF, schemas, errors, rate limits, audio containers and duration,
and voice-input configuration. The browser rehearsal uses explicitly mocked
Gemini responses and synthetic browser audio input to test the actual selection,
reference playback, WAV capture/replay/upload and cleanup UI. Those fixtures are
test data, not a fake production provider or proof of model pronunciation quality.

The owner supplied credentials through Doppler and confirmed permitted voice
inputs. Development now enables the live-tested `gemini-3.8-flash` text/audio and
`gemini-3.8-flash-tts` models. Live text/TTS/audio and the complete Edge flow passed
with generated public speech as the microphone source. This verifies integration;
it does not verify a real learner's pronunciation. A human/reference-annotated
pronunciation benchmark, including
same-transcript/different-articulation cases and multiple accents, is required
before claiming reliable phonetic error detection. Keep that acceptance item
open until real results exist. Do not replace it with LLM self-grading.

Core integration must also preserve the independently developed #48 library,
its manifests/seeding, and the #40/#41 audio-resume/accessibility regressions.
No live deployment or submission follows from local tests.

To repeat credential-free checks, run `python manage.py test`. Optional browser
rehearsal: install Playwright in the development environment, install its Chromium
or set `ASSISTANCE_BROWSER` to a local Chrome/Edge executable, then run
`python manage.py test scripts.check_assistance_browser`. It uses a temporary
database, mocked provider responses and synthetic microphone audio.

An explicit live smoke consumes provider quota:
`python manage.py check_gemini --media-id ID --paragraph 0 --start START --end END --locale fr-FR`.
Supply a published local passage and codepoint offsets. It prints status, model,
timing and audio duration rather than content/keys; `--include-audio` analyzes
generated public reference audio. The opt-in full browser smoke is
`NC_LIVE_GEMINI=1 python manage.py test scripts.check_assistance_live`, with the
backend Gemini environment injected. Use local SQLite (`DATABASE_URL` empty),
never a shared database. This generates a temporary public speech file solely
for fake microphone input; cleanup removes it at exit. See
[acceptance evidence](docs/reviews/gemini-acceptance.md) for exact checks/limits.
