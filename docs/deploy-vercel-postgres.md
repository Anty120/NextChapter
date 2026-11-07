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
