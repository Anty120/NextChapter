# Accessibility review — issue #24

## Result and review boundary

**Report complete; product accessibility approval remains open.** The tested demo
supports the exercised keyboard actions and fits the requested mobile widths.
Three findings below need coordinator triage. A real screen-reader pass and
sound-enabled human playback check remain open; this review does not establish
screen-reader usability or full WCAG conformance.

- Issue: <https://github.com/Anty120/NextChapter/issues/24>.
- Tested source: `19c479ffe15b34c953f0e26080c5bf40acc4fe76`, fetched from
  `origin/main` on November 7, 2026. All application checks used that commit.
- Environment: macOS host, real **headless Google Chrome 156.0.8078.80**, driven
  through Playwright 1.64.1. Desktop viewport: 1440 × 1050 CSS pixels; mobile
  layout viewports: **320 × 844** and **390 × 844** CSS pixels. These are desktop
  browser viewports, not physical phones or mobile Safari.
- Setup: new worktree-local `.venv`, pinned requirements installed with
  `--require-hashes`, new `db.sqlite3`, migrations and `seed_demo`. Runtime database
  readback confirmed `django.db.backends.sqlite3` and this worktree's database.
  Generated local accounts were used; no passwords or databases are committed.
  No provider credentials or shared remote database were used.
- App URL: `http://127.0.0.1:8024/`; started with Django `runserver --noreload`.
- Edit scope: this report only. Application source, migrations, dependency files,
  assets, and shared demo documents were not edited.

Entire Brain and Graph were attempted as required by the repository guide, but
both returned `command not found: entire`. Direct source inspection was used for
those queries. Sandbox restrictions initially prevented package downloads,
browser startup, and listening on localhost; the checks below ran successfully
after those operations received execution approval. Early supplementary scripts
also failed on test locators and missing navigation waits; their incomplete runs
are not counted as application failures. The corrected keyboard run passed.

## Executed checks and reproducible steps

The existing `tests/browser_demo.py` ran with `--channel chrome --base-url
http://127.0.0.1:8024 --output .venv/qa` and passed. An additional browser session
used actual Tab, Enter, Space, and typed input for the actions stated below,
waiting for each page navigation to finish. Direct navigation was used between
independent flows; this was not a single uninterrupted keyboard-only journey.

| Flow and steps | Actual result |
| --- | --- |
| Catalog: select Spanish + Short story + A1 and submit; switch to C2; activate “Explore the full shelf.” | Three A1 stories, then explicit empty state, then full catalog restored. Supplementary Tab navigation reached all three selects and the submit button; keyboard submission applied the chosen filters. |
| Skip link: load `/`, Tab once, Enter. | “Skip to content” becomes visible with a blue outline; Enter focuses `main#main`. |
| Account forms: create a unique reader, log in, then log out. | Existing rehearsal created an account and completed login/logout. Supplementary run typed credentials after tabbing to each login field, then submitted with Enter; logout was also reached with Tab and activated with Enter. Account creation inputs and submit were independently keyboard reachable. |
| Reader: authenticated `/media/1/`, Tab to “Save my place at paragraph 3,” Enter, refresh; visit shelf and Resume. | Saved paragraph persisted as `#paragraph-2.paragraph.saved-paragraph`; shelf Resume points to that paragraph. Rehearsal checked the Resume href; supplementary run independently saved via Tab/Enter. |
| Club: `/clubs/1/`, Tab/Enter to Join, Tab to comment field and type, Tab/Space on spoiler checkbox, Tab/Enter to Post. | Membership persisted; comment appeared after navigation and refresh. Tab/Space on the native `summary` expanded its hidden spoiler text. |
| Report comment: Tab/Enter on that comment's report link, Tab to reason, type, Tab/Enter to Send. Repeat through the media report link at `/media/1/`. | Both targets accepted a report and returned to their source page with “Report received. A moderator can review it.” |
| Leave club, then log out using Tab/Enter. | Join control returned; comment form disappeared after leaving; public Log in link returned after logout. Existing rehearsal also checked that the comment remains. |
| Audio: `/media/7/`, wait for metadata, Tab to native audio, Space, wait for elapsed time, Space again. | Initially `paused=true`, `autoplay=false`; Space advanced time above 0.5 seconds and the second Space paused it. Native control retained its browser outline (1px); app controls exercised above had the app's 3px outline. |
| Audio persistence: existing rehearsal starts native playback, seeks to 9 seconds, pauses, waits for saved status, refreshes. | Saved position restored to at least 8 seconds and remained paused; no autoplay. No browser JavaScript errors were recorded by the rehearsal. |
| Invalid account credentials: submit unknown username/password on `/accounts/login/`. | Error text rendered, but no `aria-invalid=true` fields or `role=alert` error existed; focus was on an input. See finding A3 and human follow-up. |

### Mobile layout and visual inspection

At **both 320px and 390px**, `document.documentElement.scrollWidth` equaled the
viewport width for all nine checked routes/states: catalog, C2 empty state,
Spanish reader, audiobook, club list, club detail with comments/member form,
login, signup, and media report form. The existing rehearsal independently
passed overflow checks on its six routes at both widths. This establishes page
width behavior for those seeded states, not every possible user-generated string.

Screenshots were visually inspected for the 320px catalog, reader, player, club,
and focused skip link, plus desktop reader. The reader's context panels stack
below its text; native audio fits the narrow paper panel. Focused Skip to content
is legible and visibly outlined. The narrow shelf clips some cover lettering
despite having no page overflow (A1). The full text title below each cover remains
readable. Screenshots are local ephemeral evidence under ignored `.venv/qa/`,
not published PR artifacts; the steps above reproduce the results.

## Source and semantic inspection

- `catalog/templates/catalog/base.html:2-13`: page language `en`, viewport meta,
  header, named main navigation, one `main`, footer, focusable skip target, and
  `role=status` for server messages. Tested catalog DOM had one main, one nav,
  and one h1. This is markup evidence, not proof that a screen reader announces
  page-load messages.
- `catalog/static/catalog/app.css:1-3`: explicit 3px `#154caa` focus-visible outline
  with 4px offset for links, buttons, inputs, selects, textareas, and summaries;
  mobile layout rules; reduced-motion override. Focus styles were also measured
  during actual Tab navigation. The reader's negative-tabindex paragraph target
  receives a separate target/saved outline.
- `catalog/templates/catalog/catalog.html:6-10`, account templates, club and report
  forms: wrapping labels for filters, Django-generated labels for account/comment/
  report controls, and descriptive submit buttons. Bookmark buttons have numbered
  accessible names. Repeated “Report comment” and spoiler-summary names still
  require human evaluation in context and through a screen reader's links list.
- No `<img>` exists in the seeded catalog; covers are live text, so image alt text
  is not applicable there. Decorative logo/art/cover marks use `aria-hidden=true`.
  The card link includes the title twice and extensive metadata; the human pass
  should judge whether that announcement is needlessly repetitive.
- `catalog/templates/catalog/media_detail.html:6-8` and
  `catalog/static/catalog/player.js`: native labeled audio with `controls`, no
  autoplay attribute or script `play()` call, readable transcript, explicit
  seconds/save fallback, and live save status. Restoring `currentTime` does not
  start playback, confirmed in Chrome. Manual saving with JavaScript disabled
  was inspected in source but was **not executed** in this review.
- Color samples calculated from the source's solid sRGB colors, using relative
  luminance: ink `#171717` on shelf blue `#46b6ea` **7.80:1**, ink on orange
  `#f26b3a` **5.92:1**, muted `#555` on white **7.46:1**, subtitle `#494949` on
  purple `#c9b8f5` **5.00:1**, bookmark `#514a29` on saved yellow `#fff5cf`
  **8.14:1**, error `#9c1730` on white **8.14:1**. Focus blue on shelf blue is
  **3.45:1**. No contrast failure was found in these samples; this is not an
  exhaustive contrast audit of every state, native control, or rendered pixel.

## Findings for coordinator reconciliation

### A1 — Low: cover titles clip at 320px

**Source:** `catalog/static/catalog/app.css:1-3` (`.cover`, `.cover-title`, phone
two-column grid), `catalog/templates/catalog/catalog.html:10`.

Open `/` at 320 × 844. The first three cover-title elements extend below their
cover boxes and are cut off by `overflow:hidden`; both screenshot inspection and
bounding-box measurement confirmed this. Full titles below each cover preserve
discovery, so this is a readability defect rather than a blocked navigation flow.
The coordinator should route a small frontend adjustment. Acceptance: all seven
seeded cover titles fit or use a deliberate readable treatment at both requested
widths, while the full title and card link remain available.

### A2 — Medium: English reader controls inherit Spanish/French language

**Source:** `catalog/templates/catalog/media_detail.html:7`.

Log in and open Spanish `/media/1/` or French `/media/6/`. The `lang=es`/`lang=fr`
story container wraps both story paragraphs and the English “Save my place” /
“Saved here” buttons, including their English `aria-label` values. Those controls
inherit the story's language because they have no English override. A screen
reader may pronounce the English controls using the story voice; that spoken
effect was **not observed** here. The coordinator should route language markup
review. Acceptance: story prose retains the correct language, while English
controls have English language semantics; Kevin verifies actual pronunciation.

### A3 — Medium: invalid-login feedback has weak programmatic signaling

**Source:** `catalog/templates/registration/login.html:2` (generic `form.as_p`),
`catalog/templates/catalog/base.html:11-12`; Django authentication form output.

Submit incorrect credentials at `/accounts/login/`. Chrome displays the
non-field error, but neither credential field has `aria-invalid=true`; the error
has no `role=alert`, and the observed focused element is an input rather than an
error summary. A user relying on spoken feedback may need to search backward to
discover why submission failed. This is an observed markup/focus limitation;
whether the chosen assistive technology announces the error requires a human
test, not an automatic failure claim based solely on the absence of a live role.
The coordinator should reconcile a bounded error-feedback task after that check.
Acceptance: Kevin can discover and understand failed-login feedback without
having to explore the page blindly, and identify the next action.

## Required human follow-up — stays OPEN

**Next actor: Kevin Chen**, or a human accessibility reviewer Kevin names.
Kevin coordinates assignment; this report does not assert he has completed or
accepted the checks. Keep #24 out of Done until he records the results and the
coordinator links or reconciles outstanding fix work.

**PENDING HUMAN CHECK — screen reader:** use VoiceOver + Safari on macOS (or
record the actual alternative technology/browser/version). Traverse the public
catalog by headings, landmarks, controls, and links; apply filters and recover
from the empty state. Create/log in to an account, deliberately fail login,
bookmark and resume a Spanish/French story, and check language switching for
prose versus buttons. Operate audio, seek, pause, resume after refresh, and judge
the frequency/usefulness of save-status announcements. Join a club, create and
expand a spoiler comment, report comment/media, leave, and log out. Confirm
labels, state changes, result/error feedback, reading order, and focus after each
full-page submission. Record pass/fail and reproducible barriers for each flow.
**Automated DOM/ARIA inspection and keyboard tests do not prove this usability.**

**PENDING HUMAN CHECK — sound and physical mobile:** verify audible playback
with sound enabled, transcript usefulness, and native control operation on a
real phone/browser. Headless Chrome is muted, so advancing playback time does
not establish audible output. Check touch behavior and zoom/text enlargement;
neither physical mobile behavior nor zoom was established by viewport resizing.

## Assignment acceptance and handoff

| Assignment criterion | Result |
| --- | --- |
| Commit, browser/device/viewport, keyboard steps, actual results, reproducible failures recorded | PASS — recorded above, with headless desktop/mobile-emulation limits explicit. |
| Screen-reader result identifies technology/flow, or named human follow-up stays open | PASS through the permitted follow-up route — Kevin's named check remains OPEN; screen-reader usability is unverified. |
| Findings name paths/severity; coordinator reconciles fix issues | PASS — A1–A3 above; coordinator must reconcile existing cards before creating bounded fixes. No new issues were created by this worker. |
| Only the report is edited | PASS — report-only commit/PR required; generated environment/database/screenshots stay ignored. |

`manage.py check` passed; all **20 Django tests passed**. Tests emitted the
expected missing collected-static directory warning in this fresh development
checkout; browser-served CSS, JavaScript, and WAV loaded and the rehearsal passed.
No app change or production deployment is claimed. Coordinator reviews this
report, reconciles A1–A3, and assigns/completes the named human checks before
closing the issue. The report PR references #24 rather than closing it.
