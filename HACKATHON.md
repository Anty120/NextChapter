# NextChapter hackathon reference

**Official event:** HACK.COMS 2026 at RIT, November 7–8, 2026.
**External sources refreshed with Exa:** 2026-11-07 22:24 UTC.
**Freshness policy:** treat earlier external claims as stale until rechecked. Read
[SOURCE_VERIFICATION.md](SOURCE_VERIFICATION.md) for source status, conflicts, and retrieval limits.
**Correction:** Auth0 is not listed in the refreshed Devpost or MLH prizes; the earlier prize claim is withdrawn.

This is the team's canonical reference for event facts, sponsor recommendations,
and durable project decisions. The [GitHub Projects kanban](https://github.com/users/Anty120/projects/2)
is the source of truth for current tasks, owners, blockers, and review state.
[AGENTS.md](AGENTS.md) tells agents how to start; [COLLABORATION.md](COLLABORATION.md)
defines task reservations and handoffs. [SPONSOR_INTEGRATION.md](SPONSOR_INTEGRATION.md)
records the technical prerequisites, compatibility decisions, and proposed evidence
for each candidate. Keep facts here instead of copying them
into several instruction files. Organizer clarifications override this snapshot;
record their source, date, and exact decision when updating it.

## Confirmed decisions and implementation status

| Item | Current status |
| --- | --- |
| Shared task tracking | GitHub Projects, with real issues in Anty120/NextChapter |
| Shared secrets | **Doppler selected by Kevin on November 7, 2026** |
| Product/demo scope | Media/community language practice without formal teaching is recorded in [#10](https://github.com/Anty120/NextChapter/issues/10); the smallest demo and ownership still need agreement in #5/#10 |
| Database | D1 was provisioned in the previous setup session; Django's checked settings still use local SQLite |
| Django hosting | Decision pending in [#3](https://github.com/Anty120/NextChapter/issues/3) |
| Sponsor integrations | Entire configuration is tracked in main; runtime capture and product integrations are not verified here |
| Prize categories | Recommendations below; none selected or submitted by this work |
| Entire | Hooks and Graph/Brain guidance are tracked; executable/destination/capture verification remains separate from committed configuration |

## Event requirements

All times are **EST, America/New_York, UTC−05:00**.

| Milestone | Local time |
| --- | --- |
| Build/submission window opens | November 7, noon |
| Category lock and initial Devpost | November 8, 9 a.m. |
| Stop development; final Devpost due | November 8, noon |
| Judging starts, per overview | November 8, 12:30 p.m. |
| Winners announced, per schedule | November 8, 5 p.m. |

Enter at most **three categories**; win at most **one**. No MLH exception is stated.
Present/demo/answer questions within five minutes. All developers on a winning submission must attend prize distribution.
Sources: [overview](https://hack-coms-2026.devpost.com/) and
[schedule](https://hack-coms-2026.devpost.com/details/dates).

Teams contain 1–4 US-based full-time students and participate in person. Under-18
participants must attend RIT; the overview also lists age 17+. Each person needs
registration and a Devpost account. Submit the project description, categories,
table number, teammates, artifact links, and a public GitHub repository. Clearly
attribute AI-generated contributions and distinguish human work. Prior projects
are ineligible; preserve attribution and licenses for permitted dependencies.
Ask organizers about ambiguous reuse rather than assuming permission.
Source: [rules](https://hack-coms-2026.devpost.com/rules).

**Official-source conflicts to resolve:** the rules retain 2025 dates and an old
registration link, while the 2026 overview/schedule agree on the dates above.
The [2026 MLH registration page](https://events.mlh.com/events/14418-hack-coms-2026)
was independently rechecked through Exa; this does not verify individual registration.
The schedule leaves judging blank; its 12:30 p.m. time comes from the overview.
Use the 2026 overview for planning and obtain organizer confirmation before
submission. Include both description and table number at the soft deadline.

## Sponsor challenges and recommendations

The refreshed [Devpost overview](https://hack-coms-2026.devpost.com/?verify=20261107)
and [MLH prize list](https://www.mlh.com/events/hack-coms-0e/prizes) corroborate
these six sponsor challenges. **Auth0 is absent from both; do not target it as an
event prize without organizer confirmation.** Provider usefulness and event
eligibility are separate.

| Challenge | Published direction, summarized |
| --- | --- |
| Gemini API | Build using Gemini API |
| Entire | Demonstrate useful agent/human collaboration with its capabilities |
| Solana | Build with Solana |
| Tiger Data | Demonstrate useful, performance-oriented Tiger Data usage |
| Vultr | Use Vultr cloud infrastructure |
| GoDaddy Registry | Register a qualifying domain through the challenge |

The five general Devpost awards cover solo work, open source, a duck game,
inclusivity/cultural representation, and first-year teams. First-Year needs a
first-year majority. The refreshed Devpost response reports eleven prizes; older
five- and twelve-prize responses are not current evidence.

MLH separately lists a **SpaceXSI raffle involving Cursor and Grok Bot**, absent
from the refreshed Devpost list. Confirm its terms/entry route and interaction with
the three-category cap before treating it as an additional entry. Do not change
our development workflow solely on that listing. Sponsor-logo names were not
reverified by Exa's text extraction.

**Current recommendation:** prioritize Entire and the Inclusivity category if the
finished demo demonstrates those criteria. Gemini stays conditional on the
audience/data decision in [#33](https://github.com/Anty120/NextChapter/issues/33).
Choose another confirmed category only when the product demonstrates it; Vultr or
Tiger Data require the hosting/database decision, while a domain needs a qualifying
registration. Auth0 may still be evaluated as a login tool, with no confirmed prize.

| Candidate | Suggested evidence; not an official minimum |
| --- | --- |
| Entire | A real project session linked to a commit and useful Graph/Brain context retrieval; inspect capture contents/destination. |
| Inclusivity | A specific access/cultural barrier addressed by working media/community features. |
| Gemini | A permitted metadata-based discovery/context feature after audience/data requirements are resolved; no lessons or quizzes. |
| Vultr | The actual demo deployed there, with release/health/data persistence evidence. |
| Tiger Data | A deliberate Postgres/analytics role that contributes to the product, not an unused second database. |
| GoDaddy Registry | A qualifying domain serving the working HTTPS demo after offer/terms confirmation. |
| Solana | A useful on-chain action; no current product requirement establishes the need. |

[SPONSOR_INTEGRATION.md](SPONSOR_INTEGRATION.md) records prerequisites and proposed
verification. [SOURCE_VERIFICATION.md](SOURCE_VERIFICATION.md) separates rechecked
facts, older guides, failed fetches, and unresolved account/runtime state. Current
model/SDK versions, quotas, pricing, and account offers require their own check.

### Entire: decide capture boundaries before enabling it

The [Entire CLI](https://github.com/entireio/cli) supports Codex and records prompts,
transcripts, and changed files as commit-linked checkpoints. Its documented
checkpoint-push behavior can publish sessions along with code. With a public
repository, review the destination and contents before capture or push; automated
redaction is not a guarantee. Keep project-only sessions separate from private
conversations and secrets. Decide on private checkpoint storage or disabled
session upload before enabling shared capture.

[Graph](https://github.com/entireio/entire-graph) supports Python and offers local
code analysis without network/model calls in its built-in analyzer. It is a
reasonable first evaluation. [Brain](https://github.com/entireio/entire-brain) can
index previous sessions, invoke a model for extraction, install a watcher, and
change agent guidance. Treat those as separate decisions. Do not enable backfill,
uploads, hooks, or background processing merely because Entire is recommended.
Record actual features used and evidence; do not claim time or token savings
without measurement. Entire history does not replace the required AI disclosure.

## Doppler: the team's secrets policy

**Decision:** Doppler is the shared secrets manager. **Verification boundary:**
CLI v3.76.1 is installed on the checked Mac; workspace/project existence, teammate
membership, configuration access, stored values, and deployment injection were
not inspected or configured by this research. Track setup in [#8](https://github.com/Anty120/NextChapter/issues/8).

Proposed naming, pending the setup owner's verification:

| Setting | Proposed value |
| --- | --- |
| Project | `nextchapter` |
| Shared development config | `dev` |
| Demo/deployed config | `prd` |

Once those identifiers and teammate access are confirmed, use each teammate's
own Doppler login and inject values into the process:

```sh
doppler login
doppler setup --project nextchapter --config dev
# Example after setup and application dependencies are installed:
doppler run --project nextchapter --config dev -- python manage.py runserver
```

Doppler's CLI injects secrets as environment variables; Django must explicitly
read the agreed names. Injection alone does not replace the current hard-coded
Django setting. References: [CLI guide](https://docs.doppler.com/docs/cli) and
[service tokens](https://docs.doppler.com/docs/service-tokens).

Team rules:

- Store secret **values** in Doppler. Git, issues, Markdown, screenshots, agent
  prompts, and Entire checkpoints may contain names and setup instructions only.
- Each teammate uses their own identity. Share appropriate development-project
  access, not personal login tokens. Do not use Kevin's unrelated personal secrets.
- Grant deployed services read-only access to only their required config using a
  scoped service token or supported deployment integration. Put the bootstrap
  credential in the host's protected secret store; never in a committed file.
- Separate development from deployed/demo credentials. Do not give ordinary tests
  write access to shared remote D1. A shared secrets config does not isolate data.
- Do not print the environment or export plaintext secrets into tracked files.
  Validate access through key presence and a harmless authenticated readback.
- One claimed setup task owns changes to secret names/access. Record rotation or
  renaming by name and affected service, update consumers, verify the result, and
  revoke the old credential only after coordination.

Proposed secret names are contracts to confirm during implementation, not claims
that values exist: `DJANGO_SECRET_KEY`; `GEMINI_API_KEY` if Gemini is selected;
`AUTH0_CLIENT_SECRET` if Auth0 is selected; `CLOUDFLARE_API_TOKEN` only if the agreed
runtime needs it. Public IDs and ordinary settings are not secret values.

## Decisions that the team still owns

Use the board to assign and resolve these; update this document with the durable
result and evidence rather than allowing chat to become the only record:

1. Confirm the demo scope in #5 and choose up to three categories before the lock.
2. Confirm registration, event date corrections, table/judging arrangements, and
   any ambiguous category/reuse requirements with organizers.
3. Verify the committed Entire setup actually runs on each intended machine, and confirm its capture/checkpoint destination before sharing sessions.
4. Configure the team's Doppler project, access, names, and runtime injection;
   verify another teammate can run the application without copying secret values.
5. Complete the hosting decision in #3 and isolated Django/D1 integration in #4.

For submissions, humans retain final control over category selection, binding
terms, purchases, account changes, and final Submit. This document records
research and decisions; it is not a submission receipt.
