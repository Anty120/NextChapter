# NextChapter

## Run the local demo

Use Python 3.12 or newer. The Django app serves the catalog and frontend together;
Node/Vite is not needed for this demo.

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

- [Hackathon source of truth](HACKATHON.md): verified event requirements, sponsor research, team decisions, and Doppler secrets policy.
- [Working together](COLLABORATION.md): claim tasks and collaborate across machines.
- [Agent instructions](AGENTS.md): required starting point for coding agents.

Tasks live as issues in [Anty120/NextChapter](https://github.com/Anty120/NextChapter/issues).
The private board is owned by `Anty120` and linked to this repository's Projects
tab. New teammates need project access as well as repository access. This board
supersedes the earlier board under `kvn8888`; update tasks only on Anthony's board.

The demo uses local SQLite. A provisioned Cloudflare D1 database is a separate
setup step; the hosting and application connection decisions remain on the board.
Doppler is selected for shared secrets; team access and application injection
still need setup and verification.

Detailed setup documentation is being coordinated in issue #2. Preserve existing
team setup notes when combining them with this navigation and the shared guidance.
