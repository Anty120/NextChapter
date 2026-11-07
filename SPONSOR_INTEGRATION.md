# Sponsor integration readiness

**Exa refresh:** 2026-11-07 22:24 UTC. Repository state checked at
`57fecf5`. Read [SOURCE_VERIFICATION.md](SOURCE_VERIFICATION.md): external claims are
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
health/readiness endpoints, and a CI workflow. Current main CI is failing because
dependency hashes were removed; repair is tracked in #34. Django's built-in auth, sessions, and
admin are installed. There are no project-defined catalog/member/community models,
product login flow, or product sponsor SDKs in the checked main tree. A React/Vite
starter frontend now exists but is not connected to the Django API.

An earlier Cloudflare readback found D1 reachable with zero tables and no Worker
named `nextchapter`; this is a historical snapshot, not a newly verified account state. Django still uses local SQLite. Doppler is selected,
but team project/config access and deployed injection have not been verified.
Do not confuse these foundations with a working hosted product.

## What must be agreed first

| Decision or prerequisite | Why it matters | Existing owner/task |
| --- | --- | --- |
| Final audience and smallest demo journey | Gemini eligibility and which integrations help the product depend on this. | Kevin/Anthony; #5, #10, #27 |
| Django hosting versus a Worker runtime; one primary database | SDK compatibility, account storage, migrations, and deployment commands differ. Local SQLite is not the shared deployed database. | Kevin/Anthony; #3, then #4 |
| Catalog records with reusable media and attribution | AI should consume permitted inputs and refer to real media, not invent availability or licensing. | Catalog/content owner; #12, #26 |
| Stable local member identity and ownership rules | Login must connect to profiles, club membership, posts, private history, and moderation permissions. | Accounts/community owners; #11, #18, #21, #25 |
| Doppler project/configs and runtime injection | A key on one laptop does not configure the deployed application or another teammate. | Secrets owner; #8 |

These do not all block parallel work. Entire can be evaluated independently of
hosting; provider wrappers and mocked tests can be designed while the product
models are built. Production login, persistent user actions, and deployment still
need the chosen storage/runtime path.

## Comparison

These effort ratings compare architectural disruption; they are estimates, not
measured durations or official challenge thresholds.

| Candidate | Change to the existing direction | Readiness / recommendation |
| --- | --- | --- |
| **Entire** | Development hooks/context tools and capture policy; no application/database replacement. | Lowest disruption. Evaluate Sessions + Graph first. |
| **Gemini** | One bounded server-side feature, provider wrapper, error handling, quota controls, UI state, and a secret. | Good conditional fit after audience/data-use checks. |
| **Auth0 (optional tool)** | Member login/callback/logout, local identity mapping, sessions, and permission checks. | Technically useful; no Auth0 challenge is listed in the refreshed event pages. |
| **Vultr** | Production server/process, HTTPS, runtime secrets, durable database, and deploy automation. | Consider only as the actual hosting decision. |
| **Tiger Data** | PostgreSQL driver/settings/migrations/testing; replaces the D1 direction or adds a second owned database. | Consider with a deliberate Postgres/analytics decision. |
| **GoDaddy Registry** | Qualifying domain registration plus DNS/TLS and updated application/auth URLs. | Add after a deployment works. |
| **Solana** | Wallet/network/transaction workflow and a real product reason for it. | Defer; no on-chain requirement is established. |

The [refreshed event descriptions](https://hack-coms-2026.devpost.com/?verify=20261107)
and [MLH list](https://www.mlh.com/events/hack-coms-0e/prizes) corroborate six shared
sponsor challenges. Auth0 is not among them. MLH also lists a separate SpaceXSI
raffle; its entry/cap treatment needs confirmation. All demonstrations below are **our proposed engineering evidence**, not
published minimums or guarantees of eligibility. Sponsor-logo names were not reverified by Exa text extraction. Doppler and
Cloudflare are supporting infrastructure, not listed prize categories.

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

Suggested implementation scope if selected: tool/version setup, reviewed hooks,
a small project session, Graph activation, and sanitized demo evidence. No backend
feature or hosting rewrite is needed. Do not claim unmeasured token/time savings.

## Gemini: resolve audience and inputs before adding the feature

The current terms require developers to be 18+ and exclude API clients directed
toward or likely accessed by under-18s. Unpaid services must not receive sensitive,
confidential, or personal information; serving users in the EEA, Switzerland, or
UK requires Paid Services. Confirm the intended audience, regions, and permitted
inputs before selection. Event participation rules do not settle product/API
eligibility. Do not assume a warning or checkbox resolves an incompatible audience.
[Terms rechecked through Exa](https://aistudio.google.com/docs/terms). The audience
decision remains deferred in #33; it was not answered by this refresh.

A product-aligned first feature is: **authorized catalog metadata → suggested
discovery tags or a short context summary → human confirmation**. Validate results
against supplied records and allowed values. Avoid fabricated media, licensing
claims, lessons, quizzes, or certified proficiency claims. Do not send private
profiles, discussions, history, or moderation reports through an unpaid demo.

Proposed changes if selected:

- Add a small provider module behind the catalog service, a route, and frontend
  loading/success/error states. Suggested paths are illustrative; domain owners
  should agree on app/module boundaries before editing shared files.
- For ordinary Django, add and lock the official `google-genai` client in
  `requirements.in`/`requirements.txt`, or use its documented REST API. Keep model
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

## Infrastructure candidates: decide before changing the stack

**Vultr:** if selected as the host, add a production application server such as
Gunicorn, process/container startup, HTTPS/proxy configuration, Doppler runtime
injection, deployment credentials, and CI-gated/serialized deployment from `main`.
Choose a durable database and migration owner. A VM does not automatically connect
Django to D1 or establish database recovery. Prove the actual demo, commit identity,
health/readiness, and retained data after redeployment. Verify the account's actual
credit/billing offer; the event promotion does not establish it.
[Vultr Python deployment pattern](https://docs.vultr.com/how-to-deploy-a-fastapi-application-with-gunicorn-and-nginx-on-ubuntu-2404).
That source illustrates app-server/proxy setup; it is not a Django compatibility test.

**Tiger Data:** its service is PostgreSQL, so use it as the agreed main database
instead of D1, or justify a separately owned analytics database. For Django, add a
compatible driver, environment-based database configuration/TLS, Doppler connection
credentials, migrations, and Postgres-backed CI. Analytics additionally needs an
owned event schema and useful queries. An unused database is weak demo evidence;
D1 plus Tiger would add synchronization/ownership work. Verify free/beta plan
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

1. Kevin/Anthony settle the audience, smallest demo, runtime/database path, and
   category slots. The event permits at most three categories; preserve the
   [published deadline and conflicts](HACKATHON.md#event-requirements).
2. The secrets owner completes #8; catalog/content and accounts owners agree on
   record/identity contracts. Give each task its own owner and migration boundary.
3. Evaluate Entire alongside actual development. Build one useful sponsor-backed
   product flow, rather than spreading work across every available provider.
4. After a provider is selected, create its bounded implementation issue using the
   relevant prerequisites and observable proof above. Resolve the final audience
   decision before accepting Gemini as that feature.
5. Verify one real staging integration after mock-based tests, then the complete
   demo in #27. CI success and account creation alone do not establish integration.

Our recommendation remains **Entire + Inclusivity**, with **Gemini conditional on
its audience/data terms and a useful media feature**. Auth0 remains a possible
login tool, with no confirmed event prize; it is not our third-category recommendation.
Vultr/Tiger should follow an intentional architecture decision. These are research
recommendations; no categories or providers were selected by this document.

This audit did not install SDKs, read secret values, create accounts/resources,
change application code, enable captures/watchers, or submit anything. The remaining
owner decisions and current status belong on spike #28 and its linked issues.
