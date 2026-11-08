# Run #48 integrated acceptance evidence

Tested source commit: `c27708161533f6b8e591b95766987a3bb73b45fc` on
`run48/integration`. The subsequent evidence commit adds this report/screenshots
and clarifies the Python executable in startup instructions; application/test source
is unchanged. Initial main: `fb5e15375cf9439291a7528cd93d7cfae8cbd0d6`;
latest incorporated main: `16e7d19` (includes #57's Vercel configuration).

Environment: macOS 27.2, Python 3.12.15, Django 6.1.3, Playwright 1.64.1,
installed Google Chrome 156.0.8078.80 in headless mode. Completed November 8, 2026
at approximately 00:46 UTC. `DATABASE_URL` was unset throughout; isolated SQLite
only. No Neon, Doppler, Vercel, deployment or production data action occurred.
Entire Brain/Graph were attempted and returned `command not found`; direct source
inspection was used under the repository's documented fallback.

## Integration receipt

All four branches were merged with `--no-ff` in order, with no source conflicts:

| Scope | Exact handoff |
| --- | --- |
| #26 / PR #59 | e4b3c16a34ef71688aa1bd6dd7fb4be7255eb593 |
| #12 / PR #51 | 4402542674beb8cf17ad388873d74ad1f8bb0ae2 |
| #16 / PR #50 | 88d0fc2be56b2ef1922c2603e79f0e2a1d45b79d |
| #19 / PR #58 | fa07a52c1d87353388f4a6782cc3bf6e8a28118e |

The final fetch confirmed #12 already contained its final real-pack validation
commit. All worker PRs remain open. The #27 claim belongs to the coordinator; this
worker did not claim/release it or change board status.

## Fresh-clone command results

Final clean clone: `/private/tmp/nextchapter-run48-final`, cloned from the
committed integration branch with `--no-local`. Created its own Python 3.12 venv;
no implementation database or venv was reused. Full command stdout/stderr and exits
are in [final-commands.json](run48-evidence/final-commands.json).

| Command | Result |
| --- | --- |
| `python3.12 -m venv .venv` | Exit 0 |
| `.venv/bin/python -m pip install --require-hashes -r requirements.txt` | Exit 0; all locked dependencies installed |
| `python manage.py migrate` | Exit 0; all migrations applied to new SQLite DB |
| `python manage.py seed_demo` | Exit 0; 12 published media, four clubs, no accounts seeded |
| `python manage.py verify_demo` | Exit 0; real text/audio hashes, metadata, DB and playable paths valid |
| `python manage.py seed_demo` (second) | Exit 0 |
| `python manage.py verify_demo` (second) | Exit 0; same media IDs 1–12 and club IDs 1–4 |
| `python manage.py check` | Exit 0; no issues |
| `python manage.py makemigrations --check --dry-run` | Exit 0; no changes detected |
| `python manage.py collectstatic --noinput` | Exit 0; 139 static files copied |
| `python manage.py test --verbosity 2` | Exit 0; all 63 tests passed, none skipped |
| Production-style `collectstatic` + full suite | Both exit 0; 409 post-processed assets; all 63 tests passed |
| `python manage.py check --deploy --fail-level ERROR` | Exit 0; existing mailer and HSTS-preload warnings only |
| `python tests/browser_demo.py --base-url http://127.0.0.1:8765 --channel chrome --output .venv/qa` | Exit 0; complete Chrome rehearsal |

Production-style commands used the CI's public fixture settings with debug false,
explicit hosts and manifest static storage. See
[production-style.json](run48-evidence/production-style.json). Missing optional mail
configuration is not a claim that password-reset email works. Local test servers
were stopped after the rehearsal.

## Persistence and malformed-pack proof

After browser rehearsal, created a separate local fixture user, custom non-seed
media, an existing published legacy Zira row, membership, comment, report and saved
positions on every format. Snapshotted every field of users, media, clubs, membership,
comments, reports and progress. Two seed/verify cycles preserved all values and IDs,
with exactly the intended change: the legacy row became unpublished. Its metadata
and 17-second progress survived. The test fixture user/custom rows are not seed content.

Then changed the first manifest title to an update that must never persist and
corrupted the final song's text checksum. Invoking the actual `manage.py seed_demo`
process exited **1** with `CommandError: song-en-02: checksum mismatch:
text/song-en-02.txt`. Every database snapshot remained identical; no early-title
update or partial changes occurred. Restored the original manifest bytes in `finally`.
See [preservation.json](run48-evidence/preservation.json). The 63-test suite also covers
missing/empty assets, HTML/bad audio, traversal/escaping symlinks, invalid records and
club targets, hashed storage, CSRF, two-user privacy and legacy progress preservation.

## Browser evidence

[evidence.json](run48-evidence/evidence.json) records the successful final Chrome run:

- Each format filter returned the expected six stories, two books, two audiobooks
  and two songs. Spanish A1 stories returned three, with the C2 empty state verified.
- Complete Marianela (1,264 paragraphs / 22 chapter links) and Alice (811 / 12)
  rendered. Keyboard navigation followed the last chapter link and focused its
  paragraph. Each book and the original bakery story saved paragraph three and
  restored its highlight after refresh.
- All four recordings actually advanced playback time after native keyboard Play,
  paused, sought to 12 seconds, saved and restored there after refresh without
  autoplay. Each returned HTTP 206 with a 64-byte range and its correct MP3/Ogg MIME.
  Every recording also passed the reused `check_player_browser` helper for both
  metadata-loading orders, speed changes, paused-seek saving and no restore writes.
- Transcripts, performer/component credits and full song-lyrics absence notices
  were visible. Source links remain credited; no full lyrics were acquired or generated.
- All four clubs joined, posted a spoiler comment, refreshed, revealed it, left and
  refreshed again; leaving preserved the comment and hid the posting form. Requests
  without CSRF failed 403; valid-CSRF nonmember comments failed 403; signed-out
  progress redirected to login. A second reader saw none of the first reader's
  book bookmarks or audio positions.
- A separate staff browser session located the reported comment, read its reason,
  changed its status and notes, saved, and verified Reviewed in the report list.
- At both 320px and 390px, shelf, both long books, every player, all club pages,
  club list, story and login had no horizontal overflow. Skip-to-content keyboard
  navigation passed on every page; Enter operated bookmarks, chapter links, account,
  club and report forms, and Space operated native audio. No page script errors or
  unavailable static assets were recorded. Optional favicon 404 is outside app assets.

Screenshots are committed in [run48-evidence/](run48-evidence/), including
[catalog at 320px](run48-evidence/catalog-320.png),
[clubs at 390px](run48-evidence/clubs-390.png),
[Marianela bookmark](run48-evidence/book-es-01.png), and
[Daisy Bell restored player](run48-evidence/song-en-01.png). These four representative
screenshots were visually inspected; the other captures preserve each media's state.
Novel captures intentionally show a viewport, since entire-book screenshots exceeded
Chrome's capture limit; full-text completeness is asserted separately.

## Inventory and remaining human work

[DEMO.md](../../DEMO.md) contains copy-paste startup commands, the five-minute
walkthrough and the exact inventory: six original stories; complete Marianela and
Alice; complete Spanish/English first audio chapters (845.06125 / 796.2859375 s);
Daisy Bell and Auld Lang Syne historical sung recordings (134.5096875 / 141.5456875 s);
The Morning Pages plus book/audio/song circles. Third-party source notices,
per-component provenance and US territorial limits remain in the bundled pack.
The unsupported Zira binary/regeneration script is retired; existing row/progress
preservation is verified, not a claim that its rights concerns were resolved.

Coordinator/Kevin owns acceptance and assigning these remaining human follow-ups
on #27: full authorized song lyrics and recording/verse agreement (a content filter
blocked writing lyrics; summaries and source links are intentionally shipped),
human listening, screen-reader testing and a physical-mobile pass. Do not retry the
blocked lyric writing by another route. Automated currentTime/decode and desktop
viewports do not prove human audibility, intelligibility or assistive-tech usability.
Deployment and Neon persistence remain #29; Gemini is deferred. No main merge,
deployment, final submission or human accessibility pass is claimed.
