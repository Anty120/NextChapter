# NextChapter

## Run the local demo

Use Python 3.12 or newer. The Django app serves the catalog and frontend together;
Node/Vite is not needed for this demo. The product UI lives in
[catalog/templates/](catalog/templates/); [frontend/src/App.tsx](frontend/src/App.tsx)
is still the separate Vite starter.

```sh
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install --require-hashes -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000/. Browse without an account; use **Join us** to create
a reader account, or sign in with the local superuser. Review reports at `/admin/`.
`seed_demo` can be run repeatedly and preserves user activity. It creates no
accounts or passwords. [DEMO.md](DEMO.md) has the rehearsal checklist, verification,
content credits, and known limitations. Local data lives in ignored `db.sqlite3`.

[**Open the GitHub Projects kanban →**](https://github.com/users/Anty120/projects/2)

- [Source verification ledger](SOURCE_VERIFICATION.md): Exa evidence, withdrawn claims, freshness policy, and unresolved conflicts.
- [Hackathon source of truth](HACKATHON.md): verified event requirements, sponsor research, team decisions, and Doppler secrets policy.
- [Sponsor integration readiness](SPONSOR_INTEGRATION.md): prerequisites, required changes, and proposed verification for each candidate.
- [Working together](COLLABORATION.md): claim tasks and collaborate across machines.
- [Agent instructions](AGENTS.md): required starting point for coding agents.

Tasks live as issues in [Anty120/NextChapter](https://github.com/Anty120/NextChapter/issues).
The private board is owned by `Anty120` and linked to this repository's Projects
tab. New teammates need project access as well as repository access. This board
supersedes the earlier board under `kvn8888`; update tasks only on Anthony's board.

The local demo uses SQLite. Kevin selected **Vercel (Django) + Neon Postgres** on November 7, 2026, using Django's built-in PostgreSQL backend. `DATABASE_URL`
in Doppler `hack-coms-hackathon` is blank until Kevin provisions Neon;
implementation and verification remain in #4. D1 is not used; no working
deployment is claimed. Teammate access and runtime injection still need verification.

**Sponsor decision (Kevin, November 7, 2026): Gemini + Entire**, retaining the
existing Inclusivity/theme direction where demonstrated. Gemini implementation
uses Kevin's resolved [audience decision #33](https://github.com/Anty120/NextChapter/issues/33):
adults-only (18+) for the hackathon, assuming the team, judges and demo users are
18+ at this college hackathon. Audience no longer blocks Gemini; regions, inputs
and current provider/API terms still need checking, so full eligibility is not
proven. Entire capture evidence still needs verification.

Detailed setup documentation is being coordinated in issue #2. Preserve existing
team setup notes when combining them with this navigation and the shared guidance.
