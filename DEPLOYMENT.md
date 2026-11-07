# NextChapter deployment

## Current state and hosting decision

CI and production configuration are prepared in this branch. No hosting service,
production database, deployment credential, or automatic deploy has been created
or enabled by this work. The actual GitHub run and hosting readbacks must be
recorded on [DevOps issue #29](https://github.com/Anty120/NextChapter/issues/29).
Hosting/database choice remains in [#3](https://github.com/Anty120/NextChapter/issues/3).

The current product kanban requires durable shared data. The demo in #27 includes
joining a club, discussion, reporting/blocking, and resuming reading/playback.
Profiles, memberships, posts, reports, and saved positions must survive a deploy.
A continuously running server is not itself required: request handlers may run
on demand, with a separate persistent database. A fresh SQLite file on an ephemeral
web-service filesystem cannot serve as the shared deployed database.

Recommendation pending Kevin's decision: a standard Django service on Render
with Postgres. This changes the earlier D1 direction; do not provision or switch
databases before that decision. Render supports deploying `main` after its CI
checks pass, but requires an authorized Git provider connection. A public repository
URL alone does not enable native auto-deploy. See
[Render deployments](https://render.com/docs/deploys) and
[Render Django](https://render.com/docs/deploy-django).

Keeping D1 instead points to Python Workers with the WSGI `django-cf` backend.
Its current documentation says production requires a paid Workers plan and the
backend does not roll back transactions. Cloudflare's D1 Django example uses SQL
migrations through Wrangler rather than assuming `manage.py migrate` works.
Confirm runtime/package compatibility and schema ownership before implementing
that path. See [Cloudflare Django](https://developers.cloudflare.com/workers/languages/python/packages/django/),
[adapter limitations](https://github.com/cloudflare/workers-py/tree/main/packages/django-cf),
and [D1 Django example](https://github.com/cloudflare/python-workers-examples/tree/main/django-todo-d1).

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

`requirements.in` lists direct dependencies. Regenerate `requirements.txt` with
`uv pip compile --python-version 3.12 --generate-hashes requirements.in -o requirements.txt`
when changing them. CI installs the lock, not whatever versions are newest.

`.github/workflows/ci.yml` checks pull requests targeting `main` and pushes to
`main`. Tests use an isolated temporary SQLite database and a public test-only
secret fixture. CI does not require Doppler or access to the team's real data.
The checks reject missing model migrations and exercise health/readiness failure
behavior and production configuration guards. Only superseded CI runs are
cancelled; the eventual deployment must have its own serialization policy.

## Production configuration contract

Shared secret values belong in Doppler; see #8. Django reads environment variables.
This does not mean a Doppler project/config or deployment sync already exists.

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

Doppler injects values into a process or syncs them to a provider's runtime secret
store. Fetching values during a build does not automatically configure runtime
secrets. For Render, its documented Doppler integration syncs a chosen config to
the service. For Workers, upload only an explicit runtime-secret whitelist; never
upload CI deployment credentials to the application. Keep separate configs/access
for development, CI deployment, and the public demo as needed. References:
[Doppler Render](https://docs.doppler.com/docs/render),
[Doppler Workers](https://docs.doppler.com/docs/cloudflare-workers).

Local development defaults to local SQLite and a development-only key. The
production database backend remains unresolved; this branch does not silently
swap it or claim local SQLite is deployable shared storage. WhiteNoise collects
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

The host-specific rollback command remains pending the hosting decision. Revert
code to a known-good commit and redeploy through the same pipeline; do not assume
a code rollback reverses database changes. Retain migration history and agree on
recovery before destructive schema work. No remote production schema changes are
authorized by a local test run.
