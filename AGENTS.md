# NextChapter shared agent workflow

Read [HACKATHON.md](HACKATHON.md) for verified event requirements, sponsor
research, durable team decisions, and the Doppler secrets policy. Read
[COLLABORATION.md](COLLABORATION.md) before starting work. The shared board is
https://github.com/users/Anty120/projects/2 and issues live in Anty120/NextChapter.

- Treat external project facts as stale until rechecked. Use Exa search/fetch for
  web sources; record URL, check time, and claim status in SOURCE_VERIFICATION.md.
  A fetch can still be cached. Preserve source conflicts and failed fetches; do
  not present old prize lists, provider offers, or prior chat claims as current.
- Keep provider capabilities separate from confirmed event prizes. Auth0 is not
  listed in the refreshed event sources; do not claim an Auth0 prize without new
  primary organizer evidence. Repository/runtime success requires separate readback.
- Refresh the board and reconcile existing issues before creating tasks.
- Claim a Ready issue using `python3 scripts/kanban.py claim NUMBER --agent UNIQUE_SESSION`
  before editing. Stop if the claim fails. Save the returned claim SHA.
- Use a separate checkout/worktree and work branch for every concurrent agent.
  Preserve other people's changes. Never reset, clean, or overwrite shared work.
- Keep scope and file ownership on the issue. Coordinate shared settings, API
  contracts, dependency files, and Django migrations before editing them.
- Record actionable blockers, deferred follow-ups, owner decisions, acceptance
  criteria, and evidence in the issue and align its board status, priority, and area.
- Push a work branch and open a PR. Record actual checks and limitations. Hand off
  with the helper and a concrete note; stop editing after releasing your claim.
- Done requires verified acceptance criteria and merged code where applicable.
  Do not merge, deploy, or submit on a teammate's behalf without authorization.
- Kevin selected Vercel (Django) + Turso (hosted libSQL) on November 7, 2026;
  D1 is not used. Turso/Django compatibility is untested and being implemented in
  #4. Verify runtime configuration and persistence before claiming deployment works.
- Doppler is the shared secrets manager; project `hack-coms-hackathon` contains
  blank credential placeholders Kevin is filling in. Config/access and runtime
  injection remain to be verified; follow HACKATHON.md. Never print secret values
  or put them in Git, issues, prompts, session captures, or evidence.
- Never commit secrets, tokens, private transcripts, or unrelated local changes.
- Preserve existing hackathon guidance when combining instructions. Coordinate
  setup documentation changes through the board before editing shared files.

<!-- entire-agent:begin -->
Read .entire/agent-guide.md for this repository's workflow, source inspection, and verification guidance.
@.entire/agent-guide.md
<!-- entire-agent:end -->
