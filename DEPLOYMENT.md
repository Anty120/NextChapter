# NextChapter deployment

## Current state and hosting decision

CI and production configuration are committed on main. The checked base
`6d915f2e6198bf6d86b177e5a2a086748ac659d7`
[passed CI](https://github.com/Anty120/NextChapter/actions/runs/42424700326). No hosting service,
production database, deployment credential, or automatic deploy has been created
or enabled by this work. The actual GitHub run and hosting readbacks must be
recorded on [DevOps issue #29](https://github.com/Anty120/NextChapter/issues/29).

**Kevin's decision, November 7, 2026:** host Django on **Vercel**, with **Turso
hosted libSQL** for shared data. D1 is not used. Turso + Django compatibility is
untested and being implemented in [#4](https://github.com/Anty120/NextChapter/issues/4).
The checked settings still use local SQLite; this document records the choice,
not a working adapter or deployment.

The demo in #27 includes joining a club, discussion, reporting for staff review,
and saving reading/playback positions. [DEMO.md](DEMO.md) explicitly defers user
blocking; [AGENT_QUEUE.md](AGENT_QUEUE.md) also places profiles outside the demo.
Accounts, memberships, comments, reports, and saved positions must survive a
deploy. An ephemeral SQLite file is insufficient for shared deployed storage.
The #4 implementation must verify the Django/libSQL adapter, migrations,
transactions, runtime dependencies and persistence on the selected platform.

## Reproducible local and CI setup

Use Python 3.12 and the committed hash-locked dependencies:

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install --require-hashes -r requirements.txt
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py collectstatic --noinput
python manage.py test
```

`requirements.txt` contains the hashes restored by #35 and installs with the CI
command above. `requirements.in` is currently absent. [Issues #4](https://github.com/Anty120/NextChapter/issues/4) and
[#34](https://github.com/Anty120/NextChapter/issues/34) track restoring that direct-dependency input and verifying a repeatable lock
regeneration command; #34 maintenance is folded into #4 and does not block current CI. The previously documented
`uv pip compile --python-version 3.12 --generate-hashes requirements.in -o requirements.txt`
command cannot run from this checkout until the input is restored and verified.
Do not remove `--require-hashes`; CI installs the committed lock.

`.github/workflows/ci.yml` checks pull requests targeting `main` and pushes to
`main`. Tests use an isolated temporary SQLite database and a public test-only
secret fixture. CI does not require Doppler or access to the team's real data.
The checks reject missing model migrations and exercise health/readiness failure
behavior and production configuration guards. Only superseded CI runs are
cancelled; the eventual deployment must have its own serialization policy.

## Production configuration contract

Shared secret values belong in Doppler; see #8. Django reads environment variables.
Kevin identified Doppler project `hack-coms-hackathon`, with blank credential
placeholders he is filling in. Config/access and deployment injection still need
verification; placeholders do not establish usable credentials.

| Variable | Purpose |
| --- | --- |
| `APP_ENV=production` | Enforce deployed configuration; refuses debug mode |
| `DJANGO_DEBUG=false` | Prevent debug responses |
| `DJANGO_SECRET_KEY` | Required injected credential; no production fallback |
| `DJANGO_ALLOWED_HOSTS` | Required comma-separated exact hosts; wildcard rejected |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Approved HTTPS origins when needed for cross-origin forms |
| `DJANGO_TRUST_PROXY` | Enable only when the hosting proxy strips/sets forwarded protocol |
| `DJANGO_SSL_REDIRECT` | HTTPS redirect defaults on with debug disabled; disabling is for isolated tests/local smoke checks |
| `APP_RELEASE` | Exact deployed Git commit, returned by the health/readiness endpoints |

Production email is deliberately unconfigured until an SMTP host is supplied;
password reset or other email flows must not be claimed working. Configure
`DJANGO_EMAIL_HOST`, optional `DJANGO_EMAIL_PORT` (default 587), `DJANGO_EMAIL_USER`,
and `DJANGO_EMAIL_PASSWORD` through Doppler before using them. Development keeps
the console mailer, and tests do not send real email.

Doppler injects values into a process or a provider's runtime secret store.
Fetching values during a build does not automatically configure runtime secrets.
The Vercel implementation must wire the agreed Doppler configuration into the
Django runtime and verify key presence without printing values. Keep deployment
credentials separate from application runtime credentials and grant only the
required access. No credential values belong in Git, logs, or demo evidence.

Local development defaults to local SQLite and a development-only key. The
selected Turso production database is not yet wired into the checked settings;
local SQLite is not proof of deployed shared storage. WhiteNoise collects
and serves static assets. The one-hour HSTS policy avoids a preload commitment;
Django may warn that preload is disabled, which is intentional until the domain
and HTTPS configuration are finalized.

## Deployment acceptance and rollback

A completed pipeline must:

1. Run the CI checks for the exact `main` commit.
2. Deploy only after those checks pass; serialize deploys and prevent an older
   revision from replacing a newer one.
3. Apply the agreed schema migration path once, with an identified owner, before
   routing traffic that requires the new schema. Use backward-compatible changes.
4. Inject runtime values from the agreed Doppler config.
5. Confirm the provider's successful deployment receipt, then request `/health/`
   and `/ready/` over HTTPS and match their `release` to the expected commit.
6. Record provider/service identifiers, URL, commit, health result, and rollback
   instructions on #29. Do not call configuration alone a working deployment.

`/health/` reports process liveness and release without querying the database.
`/ready/` performs a read-only `SELECT 1` and returns 503 without connection details
when the database cannot answer. It verifies connectivity, not every table or
application feature. Run the product demo in #27 to verify actual user flows.

The Vercel-specific rollback procedure remains to be implemented and verified in #29. Revert
code to a known-good commit and redeploy through the same pipeline; do not assume
a code rollback reverses database changes. Retain migration history and agree on
recovery before destructive schema work. No remote production schema changes are
authorized by a local test run.
