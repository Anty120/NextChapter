# Django database setup for Vercel + Neon

Kevin selected Neon PostgreSQL in issue #3, replacing Turso and D1. This change
prepares database configuration; Vercel provisioning, runtime-secret injection,
and deployment remain issue #29. No Neon project or branch is created here.

## Connection contract

Without `DATABASE_URL` (including an empty/whitespace placeholder), Django keeps
the existing local SQLite database. CI uses its temporary SQLite test database
and requires no provider credentials. A nonempty URL must use `postgres://` or
`postgresql://` and include a host and database name. Percent-encode special
characters in usernames/passwords. Invalid URLs fail with a generic error that
does not echo the URL.

The URL is parsed by `dj-database-url==3.1.2` and passed to Django's built-in
PostgreSQL backend with `psycopg[binary]==3.3.8`. Connections require TLS
(`sslmode=require`); stronger `verify-ca`/`verify-full` values are preserved.
A URL requesting `disable`, `allow`, or `prefer` cannot disable TLS.
`CONN_MAX_AGE=0` closes a connection at the end of each request. Server-side
cursors are disabled for compatibility with Neon's transaction pooler.

Use Neon's **pooled hostname** (contains `-pooler`) for Vercel requests. For
migrations use the **direct hostname** of the same intended branch. The operator
must select and confirm the development branch before any write. Store/inject the
appropriate URL through Doppler `hack-coms-hackathon`, never a committed `.env`.
Do not change an existing shared secret just to run a test.

After Kevin supplies the development branch URL, run only through Doppler:

```sh
doppler run -p hack-coms-hackathon -c dev -- python manage.py check --database default
# Only after confirming the URL targets the intended development branch:
doppler run -p hack-coms-hackathon -c dev -- python manage.py migrate
```

Do not run Django's test suite against Neon/shared data: Django creates/destroys
a test database. Use a local isolated server instead. Run schema changes once
under an identified owner, independently of Vercel request startup. No new model
migration is required by this integration.

## Reproduce the dependency lock

Python target remains 3.12. `requirements.in` restores the direct dependency input,
pins existing Django/WhiteNoise/tzdata versions, and adds the parser and driver.
The test-only PostgreSQL tooling is not a runtime dependency.

```sh
python3.12 -m venv .venv
uv pip compile --python-version 3.12 --generate-hashes requirements.in -o requirements.txt
uv pip install --python .venv/bin/python --require-hashes -r requirements.txt
.venv/bin/python manage.py test
```

A second compile should produce the same lock. CI retains `pip install
--require-hashes -r requirements.txt`. The Psycopg binary distribution includes
libpq, avoiding a compiler/system-libpq requirement in Vercel's build. PyPI lists
CPython 3.12 manylinux x86_64 and aarch64 wheels; local macOS execution alone does
not prove a deployed Vercel function works.

## Isolated local PostgreSQL rehearsal

Use PostgreSQL 16 with OpenSSL support. Put the cluster and a one-day self-signed
**test** certificate under the ignored `.venv` directory; bind only to loopback.
The test cluster uses trust authentication locally and must never be exposed.
These commands assume `initdb`, `pg_ctl` and `createdb` from that local installation
are on PATH. Choose a free port if 55434 is occupied.

```sh
initdb -D .venv/pgdata -U postgres -A trust
openssl req -new -x509 -nodes -days 1 -subj /CN=localhost \
  -keyout .venv/pgdata/server.key -out .venv/pgdata/server.crt
chmod 600 .venv/pgdata/server.key
pg_ctl -D .venv/pgdata -l .venv/postgres.log \
  -o '-h 127.0.0.1 -p 55434 -k /tmp -c ssl=on' start
createdb -h 127.0.0.1 -p 55434 -U postgres nextchapter_local
export DATABASE_URL='postgresql://postgres@127.0.0.1:55434/nextchapter_local'
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_demo
.venv/bin/python manage.py seed_demo
.venv/bin/python manage.py test --verbosity 2
pg_ctl -D .venv/pgdata stop
unset DATABASE_URL
```

`tests.test_database_config.DatabaseTransactionTests` checks a committed
create/read/delete cycle and two writes followed by an intentional exception,
then confirms neither rolled-back row exists. It runs on both SQLite and local
PostgreSQL. The full suite also exercises seeded content and user interactions.

## Primary sources and verification limits

Checked 2026-11-07 through Exa (responses may be cached); PyPI wheel filenames
and package versions also checked directly over HTTPS:

- [Django 6.1 database support](https://docs.djangoproject.com/en/6.1/ref/databases/):
  built-in PostgreSQL backend and Psycopg support.
- [Psycopg binary installation](https://www.psycopg.org/psycopg3/docs/basic/install.html):
  binary extra bundles required client libraries.
- [Psycopg 3.3.8 wheels](https://pypi.org/project/psycopg-binary/3.3.8/#files):
  Python 3.12 Linux and macOS wheel availability.
- [URL parser](https://pypi.org/project/dj-database-url/): parsing, URL encoding,
  and Django connection options.
- [Neon Django guide](https://neon.com/docs/guides/django): TLS, disabling
  server-side cursors, and connection lifetime guidance.
- [Neon pooling](https://neon.com/docs/connect/connection-pooling): pooled
  application connections versus direct migration connections.
- [Vercel Python runtime](https://vercel.com/docs/functions/runtimes/python):
  Python 3.12 support. Actual deployment verification remains #29.

Runtime evidence for this PR is recorded below and on issue #4; no source claim
or installed driver alone establishes a deployed database connection.

## Recorded local result (2026-11-07)

- Python 3.12, Django 6.1.3, Psycopg 3.3.8 binary implementation.
- PostgreSQL 16.10 built with OpenSSL under `.venv/postgres`; cluster under
  `.venv/pgdata`, bound to `127.0.0.1:55434`, self-signed test TLS certificate.
  `pg_stat_ssl` confirmed TLS on the Django connection. The server was stopped
  after verification. An initial test-only `pgserver` wheel lacked OpenSSL, so
  it was replaced by this TLS-enabled source build for the actual rehearsal.
- All migrations applied; two `seed_demo` runs passed; readback found exactly
  seven media items and one club.
- Full suite: **32/32 pass on PostgreSQL**, including committed CRUD and two-write
  rollback after reading the inserted rows. **32/32 pass on SQLite** with no URL.
- `check`, migration consistency and static collection passed. Production check
  passed at error level; existing mail/HSTS warnings remain outside this task.
- Lock regenerated twice byte-identically; hash-enforced install passed. Existing
  Django, asgiref, sqlparse, WhiteNoise and tzdata versions were preserved.
- Doppler presence-only check returned **DATABASE_URL empty**. Neon connectivity
  and remote migrations remain pending Kevin supplying the intended dev branch
  URL; no cloud database writes were attempted. Vercel runtime remains untested.

## Vercel deployment preparation (#49; no deployment)

Primary Vercel sources fetched through Exa and directly over HTTPS on
**2026-11-08 00:28 UTC** (November 7 EST; responses can still be cached):

- [Django preset](https://vercel.com/docs/frameworks/full-stack/django): detects
  `manage.py`, resolves `WSGI_APPLICATION`, collects static assets, and serves
  them through the CDN; supports WhiteNoise's compressed manifest storage.
- [Python runtime](https://vercel.com/docs/functions/runtimes/python): supports
  Python 3.12 and the top-level `application` WSGI callable.
- [Project configuration](https://vercel.com/docs/project-configuration/vercel-json):
  `framework`, `buildCommand`, and per-entrypoint `functions` settings.
- [Local build](https://vercel.com/docs/cli/build): writes `.vercel/output`;
  `--yes` can pull remote environment variables, so do not use it for this
  credential-free rehearsal.

`vercel.json` selects the Django preset and configures the function identified
by `nextchapter/wsgi.py`. The existing `.python-version` pins 3.12. The new root
`index.py` exports that same WSGI callable for Python entrypoint compatibility
and the offline smoke test; the Django preset resolves the original
`nextchapter.wsgi.application`, not a separate app or `/api` function.

The build script forces a hash-checked reinstall from `requirements.txt` and
runs Django's configuration check. A reinstall matters because Vercel installs
dependencies before invoking the script; ordinary pip installation can skip hash
verification for already-installed distributions. The Django preset then runs
`collectstatic` automatically. We choose **Vercel CDN static output**, preserving
WhiteNoise's existing storage configuration and local behavior. There is no
catch-all rewrite to swallow static URLs, and no duplicate manual static build.

### Credential-free local build

Use Vercel CLI 50.38.0 or newer, Python 3.12, and uv 0.9.25 or newer. The rehearsal
used CLI 58.5.1 and task-local uv 0.13.7. Linking selects the existing project;
it does not connect Git or deploy. Current CLI linking also creates `.env.local`
with an OIDC credential: delete that file without printing it. Do not commit
`.vercel/`, generated `pyproject.toml`, or `uv.lock`; this repository's dependency
source remains its hash-locked requirements.

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install 'uv>=0.9.25'
vercel link --yes --project nextchapter --scope kvn8888s-projects
# Remove the CLI-generated credential file without reading it.
rm -f .env.local
```

The CLI needs local project settings as well as the project IDs. To avoid
pulling provider secrets, add these **local-only fixture settings** to the
linked `.vercel/project.json`, preserving the link IDs. This rehearses the
committed config, not the remote project's environment configuration:

```sh
python3.12 - <<'PY'
import json
from pathlib import Path
p = Path('.vercel/project.json')
data = json.loads(p.read_text())
data['settings'] = {
    'framework': 'django', 'buildCommand': 'sh scripts/vercel_build.sh',
    'installCommand': None, 'outputDirectory': None,
    'rootDirectory': None, 'nodeVersion': '22.x',
}
p.write_text(json.dumps(data))
Path('.vercel/.env.preview.local').write_text(
    'DATABASE_URL=\nAPP_ENV=test\nDJANGO_DEBUG=false\n'
    'DJANGO_SECRET_KEY=local-build-fixture-not-a-deployment-secret\n'
    'DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,testserver\n'
    'DJANGO_SSL_REDIRECT=false\n'
)
PY
PATH="$PWD/.venv/bin:$PATH" vercel build
```

Do this in a dedicated checkout without injected provider credentials. Do not
use `vercel build --yes`, `vercel pull`, or `vercel env pull` for this rehearsal.
The public fixture key above is only for offline builds and tests; never use it
in a deployment. SQLite is a build/test fallback, not durable Vercel storage.
The CLI may add ignore patterns during linking; those local side effects are
not part of this change.

Recorded result: `vercel build` exited 0 and emitted Build Output API v3 output,
`functions/django.func` with runtime `python3.12` and duration 60 seconds, and
static CSS, JavaScript, and bundled audio under `.vercel/output/static/static/`.
The generated handler resolves `nextchapter.wsgi.application`. Local builds
contain macOS dependency artifacts/file mappings: build on Vercel for the
Linux deployment rather than uploading these local artifacts as prebuilt output.
The offline suite passes 37 tests, including a real WSGI `/health/` request
through `index.application` with SQLite and no provider credentials. The existing
mail configuration warning remains; email delivery needs its own configuration.
No cloud database migration, deployment, environment update, or Git connection
was performed.

### Proposed #29 release and migration step (not executed)

The #29 release owner must first verify that Kevin has supplied the intended
Neon branch credentials in Doppler and that the deployment receives the pooled
`DATABASE_URL`. Configure `APP_ENV=production`, `DJANGO_DEBUG=false`, a private
`DJANGO_SECRET_KEY`, explicit `DJANGO_ALLOWED_HOSTS`, and HTTPS
`DJANGO_CSRF_TRUSTED_ORIGINS` for each intended hostname. Set `APP_RELEASE` to the
released commit. Do not allow all `*.vercel.app` tenants or use a wildcard host.
The existing settings accept these variables; no settings or requirements patch
is requested by #49. Proxy-header trust must be verified at the host before
setting `DJANGO_TRUST_PROXY=true`; verify HTTPS behavior and secure cookies.

Before releasing code that requires a schema change, one named release owner
runs `python manage.py migrate --plan`, reviews it, then runs
`python manage.py migrate --noinput` once through Doppler against the **direct**
Neon URL for the confirmed branch. Use a separately approved release config
whose `DATABASE_URL` targets that direct endpoint; requests keep using the pooled
URL. This config is a proposal, not an existing verified Doppler config. Never
print the URL, and never copy it into a shell command, issue, or tracked file.
For example, after that config exists and its target is confirmed:

```sh
doppler run -p hack-coms-hackathon -c RELEASE_CONFIG -- python manage.py migrate --plan
doppler run -p hack-coms-hackathon -c RELEASE_CONFIG -- python manage.py migrate --noinput
```

Neither the build script nor WSGI startup migrates or seeds: concurrent previews
must not race to change a shared schema. Use backward-compatible migrations
while the previous release is serving requests. A preview that needs different
schema/data must use its own Neon branch and an explicit migration owner.
After the separately authorized #29 deployment, verify `/health/` shows the
released commit, `/ready/` succeeds, static CSS/audio load, login and saving work,
and a saved record survives a fresh function invocation. Keep #29 open until
that live evidence exists; successful local output alone does not prove hosting
or remote persistence.
