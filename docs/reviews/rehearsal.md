# Independent fresh-checkout rehearsal — issue #27

Rehearsed on 2026-11-07, approximately 23:12–23:18 UTC, by Orca Sol worker
`orca-sol-2883f57f` on branch `review/issue-27-sol`.

**Result: setup and required Django commands PASS; full browser rehearsal FAILS
at automatic audio resume after refresh.** The report is complete, but the demo
must not be declared fully rehearsed until that failure is resolved or explained.

## Baseline and isolation

- `git fetch origin && git log -1 origin/main` exited 0 after sandbox access was
  granted. Tested main/HEAD: `19c479ffe15b34c953f0e26080c5bf40acc4fe76`
  (merge of PR #32); no application changes during this review.
- Fresh Orca worktree; verified `db.sqlite3` did not exist before migration.
  New `.venv`, new worktree-local SQLite database, new reader accounts and one
  newly created local superuser. No existing author's database/account was used.
- macOS 27.2 (26B123), Apple Silicon; Python 3.12.15; Django 6.1.3;
  Playwright 1.64.1; installed Google Chrome 156.0.8078.80, headless.
- The shell's default Python was 3.10.7. Used the installed `python3.12`
  explicitly to satisfy README's Python 3.12+ requirement.
- Settings inspected: `nextchapter/settings.py` uses worktree-local SQLite.
  No provider credentials or remote D1 writes were used.
- Claim SHA: `0d5e58b188ec34c0cef554e82940c76d73071fd1`.

## Exact setup and verification commands

Commands below ran from the worktree root. After activation, `python` resolves to
its new virtualenv. Exit codes are the actual observed process/command results.

| Command | Exit | Observed result |
| --- | --- | --- |
| `python3.12 -m venv .venv` | 0 | New environment created |
| `source .venv/bin/activate` | 0 | Subsequent Python 3.12.15 |
| `python -m pip install --require-hashes -r requirements.txt` | 1 initially; 0 on retry | Initial sandbox DNS restriction; same command with network access installed all five locked requirements |
| `python manage.py migrate` | 0 | Applied admin/auth/catalog/contenttypes/sessions migrations to new SQLite |
| `python manage.py seed_demo` | 0 | Seven media items and The Morning Pages |
| `python manage.py createsuperuser --noinput --username staff-rehearsal --email staff@example.invalid` | 0 | Fresh superuser; password generated privately at runtime and passed only through child-process environment |
| `python manage.py runserver 127.0.0.1:8767 --noreload` | running during checks | Local HTTP requests succeeded; alternate port isolates this rehearsal |
| `python manage.py check` | 0 | No issues |
| `python manage.py makemigrations --check --dry-run` | 0 | No changes detected |
| `python manage.py seed_demo` | 0 | First required repeated seed |
| `python manage.py seed_demo` | 0 | Second required repeated seed |
| `python manage.py collectstatic --noinput` | 0 | 133 files copied |
| `python manage.py test` | 0 | 20 tests passed in 1.540 seconds; isolated test database destroyed |
| `python -m pip install playwright` | 0 | Optional browser tool installed only in ignored virtualenv |
| `python tests/browser_demo.py --channel chrome --base-url http://127.0.0.1:8767 --output .venv/qa` | 1 | Timed out at audio resume assertion, detailed below |
| `python .venv/staff_rehearsal.py` | 0 | Separate staff browser context reviewed report and reopened saved changes |
| `python .venv/followup_rehearsal.py` | 0 | Slower audio case, remaining mobile/community/logout checks |
| `python .venv/reproduce_audio.py --channel chrome --base-url http://127.0.0.1:8767 --output .venv/qa/reproduce` | 1 | Same sequence reproduced resume failure with diagnostic state |
| `python .venv/nojs_rehearsal.py` | 0 | JavaScript-disabled manual seconds form saved and persisted 17.0 seconds |

Additional post-activity `python manage.py seed_demo` runs both exited 0. A Python
Django ORM snapshot of every membership, comment, progress and report row before
and after those runs compared equal, including review notes and timestamps. This
checks preservation with real rehearsal activity, beyond an empty seed rerun.

The helper scripts above are local, ignored rehearsal artifacts, not application
changes. The staff helper reads runtime-generated credentials, opens a separate
Chrome context, navigates `/admin/catalog/report/`, edits Status and Review notes,
saves, reopens and asserts both persisted values. The follow-up helper logs into
a fresh context, plays the recording, pauses before seeking to 12 seconds, waits
for save completion, refreshes, checks all six routes at each mobile width, then
joins/posts/leaves/logs out. The diagnostic helper executes an unchanged copy of
`tests/browser_demo.py` with only a state print before the failing assertion and
a shorter 10-second timeout. The no-JavaScript helper uses a browser context with
JavaScript disabled and submits the normal manual save form. No helper or password
is committed.

## Observed user and staff journey

| DEMO.md step/check | Result and evidence |
| --- | --- |
| Anonymous catalog/filter | PASS: Spanish + Short story + A1 displayed exactly three cards; C2 displayed the empty state and full-shelf link |
| Read bakery story/context/credits | PASS: story paragraphs, editorial difficulty, cultural context and AI-assisted content attribution visible; desktop screenshot inspected |
| Join us/account/login | PASS: generated unique reader created through signup form, then logged in through normal UI |
| Paragraph-three bookmark | PASS: saved with Enter, refresh highlighted `#paragraph-2`, shelf Resume linked to that paragraph |
| Audio loads/plays/seeks | PASS for playback mechanics: native Play advanced currentTime beyond one second; seek to nine seconds updated input; saved message appeared; server served bundled WAV as HTTP 206 |
| Audio refresh/resume | FAIL for original native-control sequence, twice; saved value nine seconds but refreshed player remained zero; separate pause-before-seek case successfully restored 12 seconds and stayed paused |
| Transcript | PASS: text visible below player; inspected player screenshot |
| No-JavaScript manual saving | PASS: set seconds to 17, submitted Save listening position with Enter, refreshed and read back 17.0 |
| Club join/comment/refresh | PASS: membership and spoiler comment persisted after refresh; spoiler content expanded using its disclosure |
| Leave club | PASS: existing comment stayed visible, join button returned, comment form disappeared |
| Report comment | PASS: authenticated submission displayed Report received and produced report in staff admin |
| Staff report review | PASS: separate Chrome context logged into admin, opened report, changed Open to Reviewed, added notes, saved and reopened; both fields persisted |
| POST-backed logout | PASS: Enter on Log out returned login link; anonymous story stayed accessible and bookmark buttons were absent |
| Mobile overflow | PASS: document width no larger than viewport at 390px and 320px for `/`, `/media/1/`, `/media/7/`, `/clubs/`, `/clubs/1/`, `/accounts/login/` |
| Keyboard | PARTIAL PASS: Skip to content received Tab focus, Enter focused main; Enter used for bookmarking, joining, posting, report submission, leaving and logout; exhaustive focus-ring/native-audio keyboard audit pending below |
| Browser JavaScript errors | Follow-up journey recorded none; original run stopped at resume timeout and never reached its final global error assertion |

Screenshots retained locally in `.venv/qa/`: desktop catalog/reader/player,
320px/390px catalog, mobile club, and admin report. Inspected the 320px catalog,
desktop reader/player, mobile club and admin report images: text and controls are
legible, reader context is separate, the paragraph highlight and staff saved fields
are visible, and the mobile shelf has two columns. These local files are not
published PR artifacts; the textual observations above are the durable evidence.

## Findings and next actions

### P1 — saved audio timestamp does not reliably restore in Chrome

Source paths: `catalog/static/catalog/player.js` (loadedmetadata resume handler,
automatic saves), `catalog/templates/catalog/media_detail.html` (audio element and
deferred script), `tests/browser_demo.py` (audio section, approximately lines 80–96).

Reproduction on this baseline:

1. Start the new seeded database and server as above; run the committed browser
   rehearsal with `--channel chrome`.
2. Create/login a reader and reach The Blue Door through the scripted journey.
3. Native Play advances beyond one second; set currentTime to nine, then click the
   native control to pause; saved message appears and seconds input is at least nine.
4. Refresh immediately. The original run timed out after 30 seconds waiting for
   currentTime >= 8. A second run with state diagnostics printed
   `{time: 0, saved: '9.0', paused: True, ready: 4}` and timed out after 10 seconds.

This proves a saved timestamp was rendered into the refreshed page while the
player remained at the beginning in the diagnostic run. It does not establish the
root cause. The restore code only registers a `loadedmetadata` listener, making
metadata/event timing worth investigating; save/refresh timing also needs review.
A slower independent case that paused first, sought to 12, waited for save
completion plus 500 ms, and refreshed returned
`{time: 12, saved: '12.0', paused: True, ready: 4, duration: 38.824354}`.
That passing variant does not cancel the two failed original runs.

Next actor: coordinator assigns a frontend fix/investigation, reconciles this
finding into an existing or new follow-up issue, and requests rerun of the exact
committed browser test on Chrome with cached and uncached audio. Acceptance: the
original sequence restores its persisted timestamp, remains paused and completes
the full test reliably. No fix or new issue was created by this report worker.

### Tooling/environment limits

Initial Git metadata/network access and pip DNS were blocked by the local sandbox;
authorized access resolved them. `entire brain brief` and each required
`entire graph query` attempt exited 127 (`command not found`), so corresponding
source questions used direct source inspection. No Entire tool installation,
configuration or capture was performed. These are workstation/tooling limits,
not Django failures.

## Pending human checks

- **PENDING HUMAN CHECK:** listen with sound enabled to confirm audible output,
  narration intelligibility and quality. Headless playback/time advancement does
  not prove a person heard it.
- **PENDING HUMAN CHECK:** screen-reader pass with the person's chosen assistive
  technology; no screen-reader outcome is claimed.
- **PENDING HUMAN CHECK:** complete Tab order and visible focus rings across every
  filter/form/control, plus native audio controls operated only by keyboard.
- **PENDING HUMAN CHECK:** coordinator reviews the report, routes the P1 finding,
  and decides whether the demo is ready after its retest. This report does not
  establish deployment, production operation or a human submission.

## Assignment acceptance and handoff

| Issue #27 acceptance criterion | Status |
| --- | --- |
| Tested commit, OS/Python/browser, exact startup and outcomes recorded | PASS |
| Required Django command suite, two seed runs, static collection, tests | PASS |
| Browser results for all named user/staff flows recorded | PASS as a reporting deliverable; audio resume has an explicit FAIL |
| Failures include reproduction/evidence and no passwords/secrets committed | PASS |
| Only report edited; no application/dependency/migration/shared-doc changes | PASS |

Next actor is the coordinator/reviewer: review this report-only PR, reconcile the
P1 follow-up without closing the product work, and arrange the human checks above.
Issue #27 should remain Review until the coordinator verifies its acceptance;
this PR references the issue and intentionally does not close it.
