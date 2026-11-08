# Run #48 integration and handoff

The current execution scope is [#48](https://github.com/Anty120/NextChapter/issues/48),
coordinated through [#27](https://github.com/Anty120/NextChapter/issues/27).
It supersedes the earlier report-only queue and seven-item/one-club exclusions.
Initial base: `fb5e15375cf9439291a7528cd93d7cfae8cbd0d6`; main through `16e7d19`
was incorporated before fresh-clone verification.

| Scope | Worker branch / PR | Integration responsibility |
| --- | --- | --- |
| #26 content/assets | run48/issue-26 / #59 | Two complete books, two audio chapters, two sung recordings, provenance and checksums |
| #12 seed/verify | run48/issue-12 / #51 | Validate real pack before atomic writes; preserve IDs/activity; read-only verify_demo |
| #16 reader/player | run48/issue-16 / #50 | Complete text, chapter contents, private bookmarks, MIME-aware player and resume |
| #19 clubs | run48/issue-19 / #58 | Four featured-media clubs with welcoming prompts and real membership/comments |
| #27 integration | run48/integration | Merge all four, retire unsupported WAV/script, fix old tests, fresh-clone/browser/CI verification, one PR |

Workers have handed off their scopes. The coordinator retains the #27 claim;
this integration worker neither claims/releases it nor changes board status.
Worker PRs remain open; no main merge is authorized by this assignment. See the
integration PR and [verification record](docs/reviews/run48-integration.md) for exact
commits, commands, evidence and remaining checks. Review does not mean merged or deployed.

Actionable human follow-ups stay recorded in #27 and the integration PR: full song
lyrics/recording agreement (summaries and links shipped; blocked lyric writing must
not be retried), human listening, screen-reader checks, and physical-mobile checks.
Kevin/coordinator assigns those checks and accepts their evidence before calling
them verified. Deployment and Neon persistence belong to #29. Vercel + Neon Postgres
is the selected hosting; this local delivery uses SQLite, with DATABASE_URL unset.
Doppler access/injection remains separate; Gemini is deferred. Do not touch credentials.

For new work, refresh the board, reconcile existing issues, follow
[COLLABORATION.md](COLLABORATION.md), use UTF-8 mode for the helper, and claim a Ready
issue before editing. Preserve other claims, including separate #31 work. Each concurrent
agent needs a separate worktree/branch and bounded file ownership. Schema/settings,
dependencies and migrations need a coordinated single owner. Record acceptance,
blocker, next actor and actual evidence in the real issue. Never weaken the hash lock,
force-push another branch, deploy, submit or seed shared databases without authorization.
