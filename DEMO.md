# Run #48: full local library rehearsal

This integration implements [#48](https://github.com/Anty120/NextChapter/issues/48)
and [#27](https://github.com/Anty120/NextChapter/issues/27). Initial main was
`fb5e15375cf9439291a7528cd93d7cfae8cbd0d6`; main through `16e7d19` was incorporated
before final checks. Django serves the entire interface; the React starter is separate.

## Fresh-clone startup

Use Python 3.12+ in a local development shell. The following macOS/Linux commands
explicitly select SQLite and do not contact Neon, Doppler or Vercel:

```sh
git clone --branch run48/integration https://github.com/Anty120/NextChapter.git
cd NextChapter
unset DATABASE_URL
export APP_ENV=development DJANGO_DEBUG=true DJANGO_SSL_REDIRECT=false
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --require-hashes -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py verify_demo
python manage.py runserver 127.0.0.1:8000
```

On PowerShell, remove the URL with `Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue`,
set `$env:APP_ENV='development'`, `$env:DJANGO_DEBUG='true'` and
`$env:DJANGO_SSL_REDIRECT='false'`, create the venv with `python -m venv .venv`,
and activate with `.venv\Scripts\Activate.ps1`. The remaining Python commands are identical.
Open http://127.0.0.1:8000/. Use **Join us** for a reader account. For staff review,
stop the server, run `python manage.py createsuperuser`, and restart it; choose your
own credentials. No accounts or passwords are seeded. Local data is ignored `db.sqlite3`.
After dependency installation, reading, seeding and playback work offline with no
provider account, TTS engine, ffmpeg, or runtime download.

## Bundled inventory and rights

| Format | Stable slug | Content |
| --- | --- | --- |
| Book | book-es-01 | Marianela, complete Spanish text, 22 chapters / 1,264 paragraphs |
| Book | book-en-01 | Alice’s Adventures in Wonderland, complete English text, 12 chapters / 811 paragraphs |
| Audiobook | audiobook-es-01 | Marianela Chapter I, Maritza Mateo / LibriVox, 845.06125 seconds, MP3 |
| Audiobook | audiobook-en-01 | Alice Chapter I, Kara Shallenberg / LibriVox, 796.2859375 seconds, MP3 |
| Song | song-en-01 | Daisy Bell, Harry Dacre / Edward M. Favor (1894), 134.5096875 seconds, Ogg |
| Song | song-en-02 | Auld Lang Syne, Burns/traditional / Frank C. Stanley (1910), 141.5456875 seconds, Ogg |

Six original Spanish/French short stories remain, for 12 published media items.
Both audiobook recordings contain complete first chapters, labeled **chapter excerpt**
with actual lengths. These are human historical/LibriVox recordings, not generated voices.
The four clubs are The Morning Pages, a book circle, an audiobook circle, and a song
circle; each has featured media and a welcoming discussion prompt. No fake participants
or comments are seeded. Difficulty B2/C1 on the new material is an editorial estimate,
not a certification or a claim that the work is beginner Spanish.

[The manifest](catalog/demo_library/media.json) records per-component provenance,
territory, MIME, durations, chapter indexes and SHA-256 checksums.
[SOURCES.md](catalog/demo_library/SOURCES.md) and
[LICENSES.md](catalog/demo_library/LICENSES.md) retain source URLs, check times,
modifications and US public-domain scope. Check local law before redistribution
outside that scope. Complete Gutenberg source notices are bundled. Third-party
works do not inherit the code's MIT license. Original fictional stories and the
shelf design's AI-assisted implementation retain their existing attribution.

**Legacy Zira disposition (#42):** the unsupported `the-blue-door.wav` and optional
Windows regeneration script were removed from the distributable tree; Git history
retains them. Seeding unpublishes an existing `the-blue-door` row without deleting
its ID, original metadata, or anyone's saved position. Fresh databases do not create
that recording. No Microsoft redistribution permission or voice consent is asserted.

## Five-minute walkthrough

1. **0:00–0:40:** Browse anonymously. Choose each Format filter: six short stories,
   two books, two audiobooks, two songs. Spanish + Short story + A1 yields three;
   changing to C2 shows the useful empty state.
2. **0:40–1:40:** Sign up and log in. Open Marianela, use its chapter contents, save
   paragraph three and refresh. Open Alice, save a different paragraph and refresh.
   Full books remain readable; bookmarks belong only to the signed-in reader.
3. **1:40–2:50:** Open each audiobook chapter, check narrator/transcript/credits,
   play briefly, seek, pause and refresh. The saved position returns without autoplay.
   Repeat with Daisy Bell and Auld Lang Syne. Songs show credited summaries and source
   links, with an explicit **Full lyrics not bundled** notice. Native audio controls
   support keyboard playback. With JavaScript disabled, use the seconds field and
   Save listening position button to save manually.
4. **2:50–4:10:** Visit all four clubs. Join, post an original comment (mark a spoiler),
   refresh, reveal it, and leave. Leaving preserves comments but removes the posting
   form. Only members may post; anonymous readers can browse.
5. **4:10–5:00:** Report a comment. In a separate staff session, inspect it at
   `/admin/catalog/report/`, change review status and save staff notes. Log the reader
   out and confirm public browsing remains available while private positions disappear.

## Repeatable validation

With the venv active and `DATABASE_URL` unset:

```sh
python manage.py seed_demo
python manage.py verify_demo
python manage.py seed_demo
python manage.py verify_demo
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py collectstatic --noinput
python manage.py test --verbosity 2
```

Seeding validates the complete pack before an atomic database update. It preserves
stable IDs, users, custom records, memberships, comments, reports, and reading/audio
positions. Verification rejects missing/empty assets, checksum mismatches, bad
containers/MIME, invalid club targets and incomplete format inventory. The suite
covers malformed packs leaving no partial writes and preserves #40/#41 regressions.

For the optional local-only browser rehearsal, install Playwright separately
(`python -m pip install playwright`), run the server in another terminal, then:

```sh
python tests/browser_demo.py --channel chrome --output .venv/qa
```

Chrome must already be installed (or install Playwright Chromium and pass
`--channel chromium`). This creates unique local readers/staff with random credentials,
exercises all media and clubs, checks actual playback time/seek/resume and HTTP 206
with correct MIME, tests CSRF/nonmember/private-progress boundaries, reviews a report
in staff admin, and checks keyboard navigation and overflow at 320px/390px. Screenshots
and `evidence.json` go into the ignored output directory. See
[run48 verification](docs/reviews/run48-integration.md) for executed results and tested revision.

## Limits and human follow-ups

- **Full song lyrics are absent:** a content filter blocked writing them. The songs
  contain credited editorial summaries and lyric source links. A human must resolve
  authorized lyrics and exact recording/verse agreement; do not retry lyric generation
  or acquire them through another route in this run.
- Human listening, screen-reader testing, and testing on a physical mobile device
  have not been done. Automated audio time advancement and desktop viewport checks
  do not prove audibility, intelligibility, assistive-technology usability, or device behavior.
- Audio saves every five seconds and on pause/seek; a crash can lose recent seconds.
  Books have chapter navigation and explicit paragraph bookmarks, not timed highlighting.
- Reports and staff review work; blocking, appeals, password-reset email and public
  content submissions remain outside this implementation.
- Hosting is **Vercel Django + Neon Postgres**, with shared secrets managed through
  Doppler. Local build configuration is merged; deployment and remote persistence
  remain unverified in #29. Gemini is deferred. No deployment, production write,
  prize eligibility, measured learning benefit or human submission is claimed.
