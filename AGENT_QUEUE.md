# Concurrent-agent work queue

Use the live [GitHub board](https://github.com/users/Anty120/projects/2) for task
status and claims. This file defines the agreed boundaries, not a second board.

## Smallest demo and current base

Anthony confirmed the scope in [#10](https://github.com/Anty120/NextChapter/issues/10#issuecomment-6713665229).
[PR #35](https://github.com/Anty120/NextChapter/pull/35) merged as
`bdff75af30d06b8ef3b5f27fe28952e793dccb33`. The demo is:
filter the shelf → open a story or bundled English audio → sign in → save a
position → join a club and comment → report content for staff review.
Use the Django-served pages. The React starter is separate and has no demo API.
Local SQLite works without provider credentials. Deployment database selection
is a separate decision in #3. No sponsor integration is needed for local reviews.

Full lyric licensing, Spanish narration, timed read-along, chapters, creator
publishing, recommendations, user blocking, and profile features remain outside
this demo. Broader issue criteria are not satisfied merely by merging #35.

## First independent assignments

| Issue | Task | Permitted edits | Verification |
| --- | --- | --- | --- |
| #27 | Independent fresh-checkout rehearsal | `docs/reviews/rehearsal.md` only | Follow `DEMO.md`; record tested commit, startup commands, browser, outcomes and failures |
| #24 | Keyboard/mobile/accessibility review | `docs/reviews/accessibility.md` only | Review 320px/390px and keyboard flows; record actual assistive technology results or a named human follow-up |
| #26 | Catalog content and credits review | `docs/reviews/content.md` only | Compare all seven seeded items and bundled audio with `DEMO.md`; record provenance/credit gaps and publication limits |

Each task is owned by the agent that successfully claims it under their own
GitHub identity. Kevin coordinates assignments; Anthony owns product decisions.
Use a separate worktree and branch for each. Reports must identify source lines,
reproduction steps, severity, and a specific follow-up issue for actionable gaps.
Reviewers do not modify application code while another review is in flight.
Fixes receive a separate bounded claim with permission to edit the affected files.
The coordinator reconciles duplicate findings before making new issues.

#34 separately covers dependency maintenance. Its original CI failure was repaired
by #35; current main CI passed at
[run 42422779448](https://github.com/Anty120/NextChapter/actions/runs/42422779448).
The direct dependency input and repeatable hash-lock regeneration documentation
still need restoration. That work owns only dependency manifests and its own
maintenance note; do not weaken `--require-hashes` or upgrade versions incidentally.

## Shared-file ownership and merge order

Anthony is the coordination contact for `catalog/models.py`, `catalog/migrations/`,
`nextchapter/settings.py`, `nextchapter/urls.py`, dependency manifests, and the
shared catalog templates/player. A new implementation issue must name its actual
editing owner before changing these files. Only one active editing claim may own
each shared file group; other work stays Blocked with the owning issue linked.
Issue #5 owns `AGENT_QUEUE.md`, `API_CONTRACT.md`, `COLLABORATION.md`, the task
template, `scripts/kanban.py`, and its offline claim tests during queue preparation.
Sponsor/source verification documentation was handled in #28/PR #32; coordinate
any follow-up with that issue rather than editing those shared files in a review.

The three reports above can merge independently; keep filenames separate.
Application fixes depend on the relevant accepted finding and must rerun Django
checks/tests. Migration changes are serialized and checked against latest main.
No task here grants permission to merge, deploy, change accounts, or submit.

## Dispatch gates

Before claiming: refresh main and the board; read the issue, current comments and
open PRs; confirm an explicit edit scope, verification, and dependency declaration.
Ready means dependencies resolved. `Depends-on: none` is explicit; otherwise use
same-repository issue numbers such as `Depends-on: #12, #13`, each closed as completed.
The helper rejects non-Ready issues, missing/malformed declarations, and unresolved
dependencies before creating any reservation. Board/API read failure also stops it.
These checks are cooperative: they do not lock files or atomically freeze dependency
status. Recheck scope before edits and stop if a coordinator changes the assignment.

Read-only PR reviews need no editing claim. To continue editing an issue in Review,
the coordinator first returns it to Ready with the next bounded change recorded.
Claims never expire automatically. Follow `COLLABORATION.md` for safe handoffs.

## External blockers

- #9: Foryx07 repository write permission is confirmed, but only Anthony can
  confirm every intended teammate's private-board access. Do not share tokens.
- #8: local Doppler metadata lookup returned `secret not found in keyring`.
  Kevin must sign in to the intended team workspace; config/access/runtime
  verification stays pending. No project or secret was provisioned by this audit.
- #3/#29: hosting/database choice and verified deployment remain pending.
- #31: the Codex Cloud mention pilot is separate; local/Orca agents can use this
  queue without it. #33 remains the deferred Gemini audience decision.
