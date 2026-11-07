# NextChapter end-of-day demo

Implementation target: the scope Anthony confirmed on November 7, 2026 in
[#10](https://github.com/Anty120/NextChapter/issues/10#issuecomment-6713665229).

## Start from a fresh checkout

Use Python 3.12+ and follow the quick start in [README.md](README.md). Activate
the virtual environment before all commands. Existing shells configured with
production environment variables should use a separate local development shell.
The application needs no frontend build, external media service, or API key.
Create your own superuser interactively; no shared password is committed or seeded.

```sh
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py seed_demo
python manage.py seed_demo
python manage.py collectstatic --noinput
python manage.py test
```

Seeding creates or updates seven stable-slug items and one club. It never resets
accounts, memberships, comments, reports, or saved positions. It does not delete
unrelated content. Only seed-owned metadata is updated on later runs. Migrations
must run before seeding. Startup and tests use local SQLite; no remote D1 writes.

## Five-minute rehearsal

1. Open `/` without signing in. Filter Spanish + Short story + A1: three stories.
   Change level to C2: an empty state offers a link back to the full shelf.
2. Open **La panadería de la calle Sol**. Read the paragraphs, cultural context,
   approximate difficulty, and credits. Create a reader with **Join us**, then log in.
3. Open the story again. Select **Save my place** beneath paragraph three. Refresh:
   the saved paragraph is highlighted. Visit the shelf: **Resume** returns to it.
4. Open **The Blue Door** (English audiobook). Press native Play, wait, pause, and
   verify the saved message. Refresh: playback is positioned at the saved timestamp
   but does not autoplay. The transcript is available below the controls. With
   JavaScript disabled, the seconds field and Save button provide manual resume saving.
5. Open **Clubs → The Morning Pages**. Join, post a comment, and refresh. Membership
   and the comment remain. Spoiler comments are hidden behind an expandable control.
   Leave: the comment remains, but the form is unavailable until joining again.
6. Report a comment or media item. In a separate staff session, open
   `/admin/catalog/report/`, inspect the report, set its review status, and add notes.
7. Log out using the POST-backed button. The catalog remains available; personal
   progress and write actions require authentication.

## Mobile and keyboard checks

- At 390px and 320px widths, check filters, cards, the reader, player, login forms,
  and club comments for horizontal overflow. Cards use two columns on phones;
  reader context moves below the text.
- Tab from **Skip to content** through navigation and the filters; use Enter to
  submit. Each field has a label and each link/button has a visible focus ring.
- Save a paragraph, join/leave a club, post a spoiler comment, and report it using
  the keyboard. Native audio controls retain browser-provided keyboard behavior.
- Check actual audio playback with sound enabled, then refresh to verify resume.
- A teammate should perform the startup and full rehearsal independently before
  declaring the handoff complete. A screen-reader pass still needs a person using
  their chosen assistive technology; semantic markup alone does not prove it.

## Models and boundaries

`MediaItem` stores format, language, editorial level, text/transcript, bundled audio
path, attribution, cultural context, and publication state. `Club` has featured
media; `Membership` is unique per user/club. `Comment` belongs to its authenticated
author and club, with spoiler handling. Only club members can post. `ReadingProgress`
is private and unique per user/item. `Report` has exactly one media/comment target,
the authenticated reporter, review status, and staff notes. All six models are
registered in admin. State changes use POST with CSRF protection and server-side
identity/permission checks. Submitted user IDs or moderation states are ignored.

Public reading/catalog/community pages require no account. Accounts are required
for saving, membership, comments, and reports. Staff alone can access Django admin.
Published media is shown to visitors; draft media cannot be opened, saved, or reported.

## Content and design credits

- The shelf layout adapts Anthony's supplied `NextChapter-shelf (1).html`: blue
  shelving, colorful typographic covers, dark borders, yellow accents. Its mock
  completion states and nonexistent reader/review links are replaced by real routes
  and persisted user state. Frontend CSS uses local system fonts and no remote assets.
- The Spanish/French stories and English adaptation are original AI-assisted demo
  writing created for NextChapter, distributed under the repository MIT license.
  The fictional scenes do not claim to represent entire cultures or regions.
- `catalog/static/catalog/audio/the-blue-door.wav` is a bundled synthetic reading
  of the original English adaptation, rendered with Microsoft Zira Desktop en-US.
  It is approximately 39 seconds and needs no online voice service. See
  `scripts/render_demo_audio.ps1` for the optional Windows-only regeneration step;
  users do not need a voice engine to play the committed recording.
- Difficulty levels are provisional editorial estimates. They are not official
  CEFR certifications, user proficiency scores, or access restrictions.

## Verification recorded for this implementation

- Django checks and migration consistency passed. The automated suite covers
  seed idempotency, filtering, permission and CSRF boundaries, persistence, HTML
  escaping, admin report review, and audio byte-range responses. It also checks
  that new comments remain visible when older comments fill a page.
- The optional browser rehearsal (`tests/browser_demo.py --channel msedge`, after
  installing Playwright in the local environment) passed real audio playback and
  seek/resume, reader bookmarks, account creation/login/logout, membership,
  comments, reporting, keyboard actions, and overflow checks on the catalog,
  reader, player, clubs, and login pages at 390px and 320px. Screenshots were
  visually inspected. Playwright is a development-only tool, not an app dependency.
- Production-style static collection and tests passed. Deployment checks have
  only the pre-existing email-delivery and HSTS-preload warnings; neither feature
  is claimed configured. Dependency versions are unchanged; hashes were added
  because CI already requires `--require-hashes`.
- A separate teammate startup/rehearsal, screen-reader pass, live deployment,
  and human submission are still pending.

## Limits of this demo

The narrowed scope includes basic reports and manual staff review, not a complete
moderation system, blocking, appeals, password-reset email, or content submission.
Songs/books are supported media formats, but the seed contains short stories and
one English audiobook; no Spanish narration or licensed song has been supplied.
Audio positions save every five seconds and on pause/seek; an abrupt crash can lose
the last few seconds. Reading uses explicit paragraph bookmarks. The sample stories
are short and do not implement chapter navigation or timed transcript highlighting.

The standalone `frontend/` React scaffold remains separate from the Django-served
demo. Hosting, remote database selection, production secrets, and submission remain
team follow-ups. A successful local rehearsal does not establish a deployed service
or a completed human submission.

Development uses WhiteNoise's `runserver_nostatic` integration so bundled audio
supports byte-range requests and native seeking/resume. See the
[WhiteNoise development guidance](https://whitenoise.readthedocs.io/en/stable/django.html#using-whitenoise-in-development).
