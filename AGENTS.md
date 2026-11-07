# NextChapter shared agent workflow

Read [COLLABORATION.md](COLLABORATION.md) before starting work. The shared board is
https://github.com/users/kvn8888/projects/7 and issues live in Anty120/NextChapter.

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
- Do not test against the shared remote D1 database. A provisioned D1 database
  does not mean Django uses it. Verify the current configuration before claiming it does.
- Never commit secrets, tokens, private transcripts, or unrelated local changes.
- Preserve existing hackathon guidance when combining instructions. Coordinate
  setup documentation changes through the board before editing shared files.
