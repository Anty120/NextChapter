# Working together on NextChapter

[Open the shared hackathon kanban](https://github.com/users/Anty120/projects/2).
Read [HACKATHON.md](HACKATHON.md) for the canonical event/sponsor reference and
the selected Doppler secrets policy. Keep task status on this GitHub Projects board.
The board is private, owned by Anty120, and linked to the repository's Projects
tab. Kevin can update and configure it, but cannot manage collaborators. Anthony
controls teammate access; Foryx07's access to this new board is not yet verified.
Repository access and project-board access are separate. New teammates need both.
This is the canonical board; the earlier board under kvn8888 is superseded.
Issues belong to Anty120/NextChapter.

## On each machine

Install Git, GitHub CLI (`gh`), and Python 3. Sign in with your own GitHub account:

```sh
gh auth login
gh auth refresh -s project
git clone https://github.com/Anty120/NextChapter.git
cd NextChapter
```

Give each agent its own checkout or Git worktree and its own branch. Two agents
must not edit the same working directory, even on one machine. Never share GitHub
tokens or Cloudflare credentials. Read `AGENTS.md` at the start of each session.

## Take one task

1. Refresh the board, read the issue and its dependencies, and choose a **Ready** card.
2. Reserve it before editing:

   ```sh
   python3 scripts/kanban.py claim 123 --agent codex-session-a
   ```

   Replace `123` with the issue number. Save the returned `claim` SHA. The helper
   assigns your GitHub account, moves the card to **In Progress**, and posts the
   agent identity. A shared remote branch named `agent-claims/issue-123` reserves
   the task. GitHub accepts only the first creation, so separate machines and
   agents sharing an account still compete for one reservation. **If the command
   fails, do not start work.** If it says the reservation succeeded but card sync
   failed, keep the returned SHA and repair or release that reservation.
3. In your own checkout, fetch main and create the work branch named in the claim
   comment. Do not make edits on the `agent-claims/` branch: it holds metadata only.
4. Stay within the issue's scope. Agree on shared API shapes before parallel frontend
   and backend work. One agent owns Django migration changes at a time; coordinate
   migration dependencies before merging. Independent task reservations cannot
   prevent conflicts in shared files.
5. Push your work branch, open a PR that references the issue, and report the
   checks you actually ran. Put blockers and decisions in the issue as they arise.

## Hand work to a reviewer or teammate

Stop editing, push your changes, and record the exact next step:

```sh
python3 scripts/kanban.py handoff 123 --claim FULL_CLAIM_SHA \
  --status Review --note 'PR: URL. Checks: RESULTS. Next: teammate reviews acceptance criteria.'
```

Use **Blocked** when another person or dependency must act, or **Ready** when you
are returning unfinished work that another agent can continue. Always name the
next actor, remaining work, work branch/commit, and relevant evidence. The helper
updates the card, posts the handoff, and deletes only the matching reservation.
A reviewer must reserve the task before changing code, then return it to Review
or finish it. Reading a PR and leaving a review does not require an editing claim.

Claims do not expire automatically. For long work, post a progress comment at
least every 30 minutes. A quiet agent may still be editing: never delete or take
over its reservation without confirming it stopped. Use
`python3 scripts/kanban.py show 123` to inspect it. If board access fails, stop editing and release only your own reservation with
`python3 scripts/kanban.py release 123 --claim FULL_CLAIM_SHA`. This bypasses board
sync, so a teammate must repair the card and record what happened. If a machine
is lost, a human must coordinate recovery and preserve the old work branch.
After confirming the old agent stopped, inspect the reservation's SHA and remove
it conditionally:

```sh
git push --force-with-lease=refs/heads/agent-claims/issue-123:FULL_CLAIM_SHA \
  origin :refs/heads/agent-claims/issue-123
```

Use the full inspected SHA; never delete a reservation unconditionally. The old
session must not resume work without a fresh claim. These are cooperative task
reservations, not a security boundary against collaborators who bypass them.

## Columns and completion

- **Backlog:** needs scope, acceptance criteria, or a decision.
- **Ready:** clear task, clear boundaries, dependencies resolved; available to claim.
- **In Progress:** one agent actively owns the task.
- **Review:** PR and verification evidence are ready for a teammate.
- **Blocked:** state why, who must act, and what unblocks the work.
- **Done:** acceptance criteria verified and relevant PR merged. For deployment,
  also verify the live result; an upload alone is not a working deployment.

Priority: **P0** blocks the demo/team, **P1** is needed for the agreed MVP, **P2** can wait.
Area: Coordination, Backend, Frontend, Infrastructure, or Demo. Use the issue
assignee for the responsible teammate and the claim comment for the exact agent.

Create real repository issues using the task template, then attach them:

```sh
python3 scripts/kanban.py add 123
```

Set Status, Priority, and Area in the board. New issues are not automatically
imported. The board is the shared record; local chat history is not a handoff.
Keep decisions, follow-ups, test results, PR links, and blockers on the issue.
Do not mark Done because an agent says it finished; verify the result first.
