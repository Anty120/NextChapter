# Sponsor integration readiness

**External-source Exa refresh:** 2026-11-07 22:24 UTC. Repository claims below
were rechecked on November 7 against main
`6d915f2e6198bf6d86b177e5a2a086748ac659d7`; this is not a new external-source refresh. Read [SOURCE_VERIFICATION.md](SOURCE_VERIFICATION.md): external claims are
stale until rechecked, and a successful fetch is not proof of uncached content.

**Correction:** Auth0 is not on the refreshed Devpost/MLH prize lists. Its technical
section below is an optional login-tool evaluation, not a sponsor-prize recommendation.
[Spike #28](https://github.com/Anty120/NextChapter/issues/28) tracks decisions;
[HACKATHON.md](HACKATHON.md) is the canonical event/team-decision reference.

## Starting point

NextChapter's current product constraints are in [#10](https://github.com/Anty120/NextChapter/issues/10):
language practice through media and community, without lessons, quizzes, formal
grammar instruction, or mandatory assessments.

The repository has Django 6.1.3, WhiteNoise, environment-based production settings,
health/readiness endpoints, and a CI workflow. [Main CI passed for the checked commit](https://github.com/Anty120/NextChapter/actions/runs/42424700326).
[PR #35](https://github.com/Anty120/NextChapter/pull/35) restored dependency hashes;
[#34](https://github.com/Anty120/NextChapter/issues/34) covers maintenance folded into #4: restoration of
the missing direct-dependency input and repeatable lock regeneration. CI is green.

PR #35 also added `MediaItem`, `Club`, `Membership`, `Comment`, `ReadingProgress`,
and `Report` in [catalog/models.py](catalog/models.py), the initial migration,
and [admin registration](catalog/admin.py). Django user accounts provide signup,
login/logout, and authenticated actions through [catalog/urls.py](catalog/urls.py)
and [catalog/views.py](catalog/views.py). The real demo UI is rendered by
[catalog/templates/](catalog/templates/); [frontend/src/App.tsx](frontend/src/App.tsx)
still renders the Vite starter and is not connected to a demo API. These local
features do not prove sponsor integration or deployment.

Kevin selected **Vercel for Django + Neon Postgres** on November 7, 2026.
Django's built-in PostgreSQL backend is the selected database backend. D1 is not
used. `DATABASE_URL` is a blank placeholder in Doppler `hack-coms-hackathon` until
Kevin provisions Neon; implementation and verification remain in #4. The checked
settings still use local SQLite; no working Neon integration or deployment is
claimed. Teammate access and runtime injection still need verification.
A hosting choice and placeholder names do not establish a working hosted product.

## What must be agreed first

| Decision or prerequisite | Why it matters | Existing owner/task |
| --- | --- | --- |
| Gemini launch regions, permitted inputs, and current provider/API terms | Kevin closed #33 with an adults-only (18+) hackathon audience; remaining implementation checks do not establish full eligibility. | Gemini implementation owner; Kevin/Anthony |
| Vercel Django + Neon Postgres implementation | Use Django's built-in PostgreSQL backend; `DATABASE_URL` in Doppler `hack-coms-hackathon` is blank until Kevin provisions Neon. Migrations, transactions and durable storage still need verification. D1 is not used. | Infrastructure owner; #4 |
| Permitted catalog inputs and attribution | Catalog models and demo seed exist; rights and publication limits still need review before provider use. | Catalog/content owner; #12, #26 |
| Broader member and moderation rules | Django accounts, memberships, comments, private positions, and reports exist; profiles, blocking, and the broader backlog remain. | Accounts/community owners; #11, #18, #21, #25 |
| Doppler project/configs and runtime injection | A key on one laptop does not configure the deployed application or another teammate. | Secrets owner; #8 |

These do not all block parallel work. Entire can be evaluated independently of
hosting; provider wrappers and mocked tests can be designed independently.
The product models already support the local demo. Production persistence and deployment still
need the selected Vercel/Neon Postgres path to be implemented and verified.

## Chosen categories and remaining gates

**Kevin's decision, November 7, 2026:** the sponsor categories are **Gemini and
Entire**. Keep the existing Inclusivity/theme direction where the working demo
supports it; this decision adds no third sponsor and is not a category submission.
Kevin closed [#33](https://github.com/Anty120/NextChapter/issues/33) on November 7:
NextChapter is adults-only (18+) for the hackathon, assuming the team, judges and
demo users are 18+ at this college hackathon. Audience no longer blocks Gemini.
Launch regions, permitted inputs, and current provider/API terms remain
implementation checks; full eligibility is not proven. Entire still needs verified
capture evidence. Vercel (Django) + Neon Postgres is selected, using Django's
built-in PostgreSQL backend. `DATABASE_URL` in Doppler `hack-coms-hackathon` is
blank until Kevin provisions Neon; #4 owns implementation and verification.

## Comparison

These effort ratings compare architectural disruption; they are estimates, not
measured durations or official challenge thresholds.

| Candidate | Change to the existing direction | Readiness / recommendation |
| --- | --- | --- |
| **Entire** | Development hooks/context tools and capture policy; no application/database replacement. | Lowest disruption. Evaluate Sessions + Graph first. |
| **Gemini** | One bounded server-side feature, provider wrapper, error handling, quota controls, UI state, and a secret. | Good conditional fit after audience/data-use checks. |
| **Auth0 (optional tool)** | Member login/callback/logout, local identity mapping, sessions, and permission checks. | Technically useful; no Auth0 challenge is listed in the refreshed event pages. |
| **Vultr** | Production server/process, HTTPS, runtime secrets, durable database, and deploy automation. | Unselected; replacing Vercel requires a new owner decision. |
| **Tiger Data** | PostgreSQL driver/settings/migrations/testing; would replace Neon or add a second owned database. | Consider with a deliberate Postgres/analytics decision. |
| **GoDaddy Registry** | Qualifying domain registration plus DNS/TLS and updated application/auth URLs. | Add after a deployment works. |
| **Solana** | Wallet/network/transaction workflow and a real product reason for it. | Defer; no on-chain requirement is established. |

The [refreshed event descriptions](https://hack-coms-2026.devpost.com/?verify=20261107)
and [MLH list](https://www.mlh.com/events/hack-coms-0e/prizes) corroborate six shared
sponsor challenges. Auth0 is not among them. MLH also lists a separate SpaceXSI
raffle; its entry/cap treatment needs confirmation. All demonstrations below are **our proposed engineering evidence**, not
published minimums or guarantees of eligibility. Sponsor-logo names were not reverified by Exa text extraction. Doppler and
the selected Vercel/Neon Postgres stack support the project; this does not make them
additional listed prize categories.

## Entire: verify the committed setup and capture boundaries

The CLI can capture sessions in an existing Git repository without an account;
Graph supports Python and local code analysis. GitHub remains the team's code,
issue, PR, and kanban home. [CLI](https://github.com/entireio/cli),
[Graph](https://github.com/entireio/entire-graph).

Main now contains hooks/configuration and Graph/Brain guidance. Runtime capture
is not verified in the parent session; the executable is unavailable on its PATH.
Before relying on the setup, agree on which project-only sessions may be captured and
whether checkpoint uploads are disabled or sent to a private destination. Its
checkpoint refs can expose transcripts through a public Git remote; redaction is
best effort. Preserve existing Git/agent hooks and our guidance when applying
managed instructions. Inspect outgoing checkpoint contents before publishing.

Proposed proof: a real agent session linked to its commit, then another agent
uses a Graph query to locate relevant code before continuing. Save the actual
query and result. A PR comment or GitHub cloud task is not automatically proof
of Entire capture. Brain is optional: default setup can process historical
sessions, call a model, and install a watcher, so decide those separately.
[Privacy](https://github.com/entireio/cli#security--privacy),
[Brain](https://github.com/entireio/entire-brain).

Remaining Entire verification scope: tool/version setup, reviewed hooks,
a small project session, Graph activation, and sanitized demo evidence. No backend
feature or hosting rewrite is needed. Do not claim unmeasured token/time savings.

## Gemini: resolve audience and inputs before adding the feature

The current terms require developers to be 18+ and exclude API clients directed
toward or likely accessed by under-18s. Unpaid services must not receive sensitive,
confidential, or personal information; serving users in the EEA, Switzerland, or
UK requires Paid Services. Confirm the intended audience, regions, and permitted
inputs before implementation. Event participation rules do not settle product/API
eligibility. Do not assume a warning or checkbox resolves an incompatible audience.
[Terms rechecked through Exa](https://aistudio.google.com/docs/terms). The audience
decision in #33 is resolved: adults-only (18+) for the hackathon. Audience no
longer blocks Gemini; regions, inputs and current provider/API terms still need
implementation-time verification, so full eligibility is not established.

A product-aligned first feature is: **authorized catalog metadata → suggested
discovery tags or a short context summary → human confirmation**. Validate results
against supplied records and allowed values. Avoid fabricated media, licensing
claims, lessons, quizzes, or certified proficiency claims. Do not send private
profiles, discussions, history, or moderation reports through an unpaid demo.

Proposed Gemini implementation with the audience decision resolved:

- Add a small provider module behind the catalog service, a route, and frontend
  loading/success/error states. Suggested paths are illustrative; domain owners
  should agree on app/module boundaries before editing shared files.
- For ordinary Django, add and lock the official `google-genai` client in
  `requirements.txt` once #4/#34 restores the missing `requirements.in` regeneration
  input, or use its documented REST API. Keep model
  selection in configuration. For a Worker runtime, prove the chosen HTTP client
  and dependencies there before accepting the integration.
- Inject `GEMINI_API_KEY` through Doppler into the backend. Add timeouts, bounded
  retry behavior, request limits, output validation, and caching where appropriate.
  API-key separation alone does not isolate a shared project's quota.
- Test success, malformed/blocked output, timeout, and quota failure using a fake
  provider. Separately record one real staging request with permitted input.

SDK/API/model and quota details remain pending a fresh implementation-time check;
the libraries fetch timed out during this Exa refresh. Prior SDK suggestions are
not runtime compatibility proof. References: [libraries](https://ai.google.dev/gemini-api/docs/libraries),
[quickstart](https://ai.google.dev/gemini-api/docs/quickstart),
[rate limits](https://ai.google.dev/gemini-api/docs/rate-limits).

## Auth0: optional login tool, not a confirmed prize

The refreshed official event lists do not include Auth0. Keep this section only
if the team chooses it for product login, not to claim a prize.

Choose Django server sessions versus a separate browser app/API design. The
Auth0 application type and token handling depend on that choice. The official
Django guide uses Authlib and a Regular Web Application. Its sample dependency
versions must be checked against our Django 6.1 lock, not copied over it.
[Django guide](https://developer.auth0.com/resources/guides/web-app/django/basic-authentication).

Proposed changes if selected: lock the compatible auth dependencies; add
login/callback/logout routes and Django auth wiring; configure exact allowed
callback/logout/origin URLs; and add the local member/profile mapping. Register
production URLs once the hostname is agreed. Local development can proceed with
its own explicit callbacks.

Use the exact identity issuer/tenant plus provider subject as the stable link to
a local member. Do not make mutable email the identity key. Keep `AUTH0_DOMAIN`
and `AUTH0_CLIENT_ID` as configuration and inject `AUTH0_CLIENT_SECRET` from Doppler.
Auth0 authenticates a person; our queries must still enforce ownership, blocks,
and moderator permissions. If protecting an API with tokens, verify signature,
issuer, audience, and expiry with a maintained library.
[Identity](https://auth0.com/docs/manage-users/user-accounts/identify-users),
[token validation](https://auth0.com/docs/secure/tokens/json-web-tokens/validate-json-web-tokens).

Proposed proof: login/logout, anonymous access denied, the same user remains
mapped after re-login, two users cannot access each other's private records, and
invalid callback state is rejected. This fits #11 and the community/privacy tasks;
it must not create a second competing member account system.

## Unselected infrastructure alternatives: research only

**Vultr:** not selected; replacing Vercel would require a new owner decision. If chosen, add a production application server such as
Gunicorn, process/container startup, HTTPS/proxy configuration, Doppler runtime
injection, deployment credentials, and CI-gated/serialized deployment from `main`.
Choose a durable database and migration owner. A VM does not automatically connect
Django to the selected database or establish database recovery. Prove the actual demo, commit identity,
health/readiness, and retained data after redeployment. Verify the account's actual
credit/billing offer; the event promotion does not establish it.
[Vultr Python deployment pattern](https://docs.vultr.com/how-to-deploy-a-fastapi-application-with-gunicorn-and-nginx-on-ubuntu-2404).
That source illustrates app-server/proxy setup; it is not a Django compatibility test.

**Tiger Data:** its service is PostgreSQL, so use it as the agreed main database
instead of the selected Neon Postgres database, or justify a separately owned analytics database. For Django, add a
compatible driver, environment-based database configuration/TLS, Doppler connection
credentials, migrations, and Postgres-backed CI. Analytics additionally needs an
owned event schema and useful queries. An unused database is weak demo evidence;
Neon plus Tiger would add synchronization/ownership work. Verify free/beta plan
limits and account terms before provisioning.
[Create service](https://www.tigerdata.com/docs/get-started/quickstart/create-service),
[connection details](https://www.tigerdata.com/docs/integrate/find-connection-details).

**GoDaddy Registry:** first obtain a working deployment URL and confirm the
challenge's eligible domain/registration path with organizers. The event listing
does not establish that any GoDaddy purchase qualifies. Then configure DNS, host
verification/TLS, Django allowed hosts/CSRF origins, and Auth0 callbacks/logout URLs.
Domain registration need not replace Cloudflare DNS or hosting. Verify registration,
renewal, and terms before purchase. Proof is the qualifying domain serving the
actual HTTPS demo. [DNS documentation](https://www.godaddy.com/help/manage-dns-records-680).

**Solana:** establish a genuine on-chain use case first. It would require wallet
connection, network/RPC configuration, a useful transaction or program interaction,
confirmation/error handling, and any mapping to local members. Do not put private
reading history, discussions, or licensed media on a public ledger. A wallet button
alone does not demonstrate useful integration. Devnet can support development, but
confirm its acceptability for the challenge. [Frontend](https://solana.com/docs/frontend),
[clusters](https://solana.com/docs/references/clusters).

## Suggested order and handoff

1. Use the smallest demo agreed in #10 and merged in #35 (see [DEMO.md](DEMO.md)).
   Kevin resolved #33 with the adults-only hackathon audience and chose Vercel +
   Neon Postgres with Django's built-in PostgreSQL backend; implementation remains
   in #4. `DATABASE_URL` in Doppler `hack-coms-hackathon` is blank until Kevin provisions Neon. Gemini + Entire are the chosen sponsor categories. The event permits at most three categories; preserve the
   [published deadline and conflicts](HACKATHON.md#event-requirements).
2. The secrets owner completes #8; catalog/content and accounts owners agree on
   record/identity contracts. Give each task its own owner and migration boundary.
3. Verify Entire capture evidence alongside actual development. Build one useful sponsor-backed
   product flow, rather than spreading work across every available provider.
4. Create bounded implementation tasks for the chosen categories using the
   prerequisites and observable proof above. Verify regions, permitted inputs and current provider/API terms during Gemini implementation.
5. Verify one real staging integration after mock-based tests, then the complete
   demo in #27. CI success and account creation alone do not establish integration.

The owner decision is **Gemini + Entire**, retaining the existing Inclusivity/theme
direction where demonstrated. #33 is closed with the adults-only hackathon
audience; remaining Gemini implementation checks and Entire capture evidence
still need verification. Auth0 is an optional login tool,
with no confirmed event prize. Vultr/Tiger are unselected research alternatives. Hosting is Vercel + Neon Postgres via Django's built-in PostgreSQL backend;
`DATABASE_URL` in Doppler `hack-coms-hackathon` is blank until Kevin provisions
Neon and #4 implements the connection. No working deployment or category submission is recorded here.

This audit did not install SDKs, read secret values, create accounts/resources,
change application code, enable captures/watchers, or submit anything. The remaining
implementation gates and current status belong on spike #28 and its linked issues.
