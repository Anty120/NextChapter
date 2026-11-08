# Project completion audit and Motion UI polish

Audit date: November 8, 2026, 04:27 UTC. Owner requested issue cleanup, next
priorities and improved UI motion. Work reservation: #74,
`43ce64175186554824785a1e315d003836c0d945`.

## Closed work

Completion was checked against actual merged PR states, current GitHub main
ancestry, issue evidence and the seeded local catalog. Each issue has its own
completion comment; its board card is Done.

| Issue | Accepted evidence |
| --- | --- |
| #3 | Kevin's final Vercel + Neon decision, implemented by merged #46. |
| #4 | Merged #46, local PostgreSQL migration/seed/CRUD/rollback checks; later production migration/seed receipt in #29. Deployment pipeline remains #29. |
| #5 | Merged #36: claim/dependency gates, queue, contracts; core run #48 completed. |
| #10 | Complete-library scope delivered in merged #65 and accepted #48/#27. Later owner requests supersede historical English-audio/no-quiz constraints. |
| #28 | Research/ledger corrections merged in #32/#44; Gemini + Entire selected, #33 audience decision, bounded #60–64 implementation created. No prize/submission claim. |
| #61 | Backend merged through #68/#69; auth/CSRF/quota/schema/WAV/privacy regressions and separate real provider receipts. Human articulation benchmark remains #64. |
| #62 | Reader assistance merged through #68/#69, with later main speed/sentence/hint changes; Unicode/mobile/keyboard and live text/TTS evidence. |
| #71 | Translation commit 0688004 is on remote main; 102-test regression, browser and real synthetic-comment translations; CI run 42441219351 passed. |
| #72 | Listening shortcut f8cbfce is on remote main; 17 catalog tests and actual HTTP readback show songs and audiobooks. |

#66 was closed **not planned**, not completed: it requested lyrics for the two
retired English recordings. Current French/Spanish songs have original context
summaries and source links. Written lyrics are not silently represented as done.
#17 records this remaining product/source decision.

#73 remains Review: its back-to-top implementation is tested on local main but
the audit's remote main (`5a45bd9`) did not yet contain it. It is not marked Done
merely because it works locally. No remote-main merge or deployment was performed.

## Focus next

| Priority | Issue / concrete next action |
| --- | --- |
| P0 | #29: verify CI-gated main releases, production/Preview isolation, APP_RELEASE and the intended live commit, durable DB data and production Gemini shared-cache configuration. Kevin/Anthony own deployment changes. |
| P1 | #64: Anthony or a consented evaluator independently annotates French/Spanish human recordings, including same words with different articulation. Retain uncertainty; synthetic speech only proves integration. #60 remains open. |
| P1 | #21: scope server-enforced blocking, conduct policy and moderator actions/reasons/appeals before a wider public community release. Existing reporting/admin is only part of this feature. |
| P2 Ready | #11: a single claimant can add private language preferences, separate reading/listening levels and an unsure option; one model/migration owner, explicit CSRF/privacy/seed-preservation/mobile checks. No demographic disclosure or content gating. |

Board fields and actionable notes were updated. #70 stays with its existing
redesign owner. No local or remote redesign branch was available in this
checkout; this task does not seize or overwrite that work. Broader unfinished
issues such as #13/#14/#15/#18/#20/#22/#23/#25/#52–56 stay open.

## UI implementation

An additive `ui-polish.css` layer makes the existing shelf calmer and clearer:
warm paper surfaces, serif display/book titles, a distinct filter tray, readable
card metadata, softer borders, rounded panels and consistent focus states. The
existing cover palette, forms, URLs, layout contracts and native players remain.

Locally vendored Motion 14.10.1 supplies spring lift/press/release for cards,
links and buttons, a bounded heading entrance and short card/result fades.
Motion never controls popup coordinates, hides paragraphs while loading, or
animates thousands of book paragraphs. Hash-linked reading positions are kept.
Animations are skipped for reduced-motion preferences; changing that preference
at runtime cancels active animations. Content and GET/POST forms work when
JavaScript or the vendor asset is unavailable. No CDN, new backend dependency,
schema, account change or billing change is involved.

The MIT license, registry integrity and browser SHA-256 are preserved in the
vendor directory. Sources/check times are in SOURCE_VERIFICATION.md. #70 has
coordination notes for the additive base imports; its owner should preserve or
deliberately consolidate equivalent behavior when rebasing the full redesign.

## Verification

Existing suites and browser rehearsals are executed against isolated local
SQLite, with provider calls mocked except for earlier recorded real receipts.
The Django suite passed 103 tests in 73.865 seconds (two Windows symlink-privilege
skips). `check`, migration dry-run, static collection and diff checks passed.
The Motion/audio-quiz/comment-translation browser group passed three tests in
22.462 seconds, including all Motion-specific checks listed below. After tightening
the mobile header, Motion plus the complete reader/microphone rehearsal passed
two tests in 76.694 seconds, including the real 60-second capture hard stop.
The final main/CI readbacks are recorded in the handoff.
The final issue handoff records exact results and commit. The browser rehearsal
checks spring transforms, press/release, 320/390/1440 widths, keyboard skip link,
reduced-motion changes, hash targets, anchored reader popup, no-CDN requests,
missing-vendor and no-JavaScript filter submission. Other rehearsals cover
audio/quiz playback and comment translation. Human screen-reader and speech
assessment are still independent open checks.

Before/after screenshots are local, contain synthetic/public catalog content and
live in the ignored `.venv/qa/` directory. Reproduce:

```sh
python manage.py test tests catalog
python manage.py test scripts.check_motion_browser scripts.check_learning_browser scripts.check_comment_translation_browser
```

For browser checks, install Playwright in the development environment and set
`ASSISTANCE_BROWSER` to a local Edge/Chrome executable if needed. Runtime assets
are normal Django static files and require normal production `collectstatic`.
