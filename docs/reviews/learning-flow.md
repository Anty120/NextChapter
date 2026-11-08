# Reader speed, sentence practice, quizzes and non-English audio

Issue #64, reservation `403859045b8650d80a09848a27a559f5b6868b51`.
The owner explicitly requested no PR for this batch. Work is verified in an
isolated checkout and then applied to clean local main; no remote merge,
deployment or submission is implied.

## Result

- Clicked words use a four-field fast lookup with separate model configuration,
  one-hour public-reference server caching, and bounded same-page caching.
  Explain more explicitly requests the original full teaching response.
- Speak expands a word selection to its whole sentence. A sentence toolbar
  provides a microphone action, explanation, and optional per-word sound hints.
  Hints preserve paragraph text and Unicode selection/bookmark positions.
- Local mono WAV capture is bounded to 60 seconds, 5 MiB, with 24 kHz requested
  sample rate. Permission, replay, discard, explicit Analyze upload and cleanup
  behavior remain. No numeric pronunciation grades are introduced.
- Both complete seeded books have five curated comprehension questions, server
  grading, CSRF, and answer explanations after submission. Results are optional
  and transient. The quiz link appears at the end with a navigation shortcut.
- Current audio: Spanish Marianela Chapter I; French complete original short
  story Le livre jaune (credited synthetic voice); French sung Tourdion; Spanish
  sung Las Mañanitas opening. All files are bundled and checksummed. Old English
  audio is unpublished on reseeding without deleting progress or user activity.

## Verification receipts

- Public French moi: earlier full adapter response 12.307 seconds; new lookup
  0.876 seconds; server-cached repeat under 1 millisecond. Single samples, not an
  SLA. Development Doppler's lookup model is `gemini-3.5-flash-lite`; full text,
  speech and audio-input models remain independently configured. No keys logged
  or stored, no billing or priority-tier change.
- Mocked-provider Edge rehearsal passed in 69.268 seconds: 320px popup,
  keyboard entry, clipboard, offsets after an emoji, escaped model markup,
  quota failure, sentence multipart reference, replay/discard, explicit upload,
  real 60-second automatic stop, denied permission, logout track cleanup, and
  hints preserving original text.
- Live-provider Edge rehearsal passed in 22.436 seconds. Actual HTTP 200 from
  lookup, pronunciation audio, sentence practice and phonetics. The reference
  text and microphone source were generated public French speech. This verifies
  integration, not calibrated pronunciation assessment.
- Local Edge playback/quiz rehearsal passed in 6.218 seconds: all four audio
  files decode, advance playback, expose durations and seek; both quizzes submit
  and render scores at a 320px viewport without horizontal overflow.
- Django regression suite and actual main seed/readback receipts are appended
  in the issue handoff after execution.

## Reproduce

Use normal startup from main with the signed-in Doppler CLI. Reseed via
`python manage.py seed_demo`, then `python manage.py verify_demo`. Sign in, open
Le livre jaune, click a word, then Speak or the sentence microphone. Choose
Pronunciation hints to reveal approximate sounds. Open either complete book and
use End-of-book quiz. Filter the shelf to Song or Audiobook for non-English audio.

Credential-free regression: `python manage.py test tests catalog`.
Optional Playwright checks: `python manage.py test scripts.check_assistance_browser scripts.check_learning_browser`.
Set `ASSISTANCE_BROWSER` to an installed Chrome/Edge executable if needed.
Live test is separately opt-in via `NC_LIVE_GEMINI=1` with injected backend
Gemini configuration and `scripts.check_assistance_live`.

## Limits

Pronunciation comparisons are approximate and model feedback is not calibrated.
Human/reference-annotated accent and articulation checks remain open from #64.
Production still needs its configured shared cache, provider credentials and
runtime verification. Existing source territory restrictions are retained.
Neither bundled song includes a written lyric transcription; the text is clearly
labeled as editorial context. The Spanish song is explicitly an excerpt.
