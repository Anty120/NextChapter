# Project knowledge: verification ledger

**Exa refresh completed:** 2026-11-07 22:24 UTC.
**Method:** Exa search and page fetches from primary publishers; Git/GitHub for
repository state. This ledger supersedes earlier unsourced or cached prize claims.

## Freshness rule — Kevin's instruction

Treat external claims as **stale/unverified until rechecked**. Use Exa for web
searches and known-page fetches. A successful fetch is not proof of an uncached
page. Record the URL, check time, claim, and status; inspect the returned content.
If sources disagree, retain the conflict and use another primary source. Do not
repeat an old claim as confirmed just because a prior chat or tool said it.

Use these statuses:

- **Rechecked:** the fetched primary source supports this specific claim at this check.
- **Not listed:** the refreshed listings do not contain the claimed category; do
  not plan a prize entry around it without organizer confirmation.
- **Conflicted:** official text or retrieved versions disagree; preserve both.
- **Pending:** a fetch failed, a guide is incomplete/old, or account/runtime evidence is absent.
- **Repository observed:** verified in a specific commit or CI receipt, not a web-product promise.
- **Team decision:** explicitly chosen by the team; separate from provider availability and working integration.

No category selection, paid-plan entitlement, service provisioning, or working
integration can be inferred from a product guide. Recheck event entries before
submission, provider terms before integration, and live state before declaring success.

## Event and prize corrections

| Claim | Status and evidence |
| --- | --- |
| Auth0 challenge / wireless-headphones prize | **Not listed.** Neither the refreshed Devpost list nor MLH's event prize page contains Auth0. The earlier claim is withdrawn. Auth0 remains an optional login tool, not a confirmed event target. |
| Shared sponsor challenges | **Rechecked:** Gemini, Entire, Solana, Tiger Data, Vultr, and GoDaddy Registry appear across the refreshed event listings. |
| Devpost prize count | **Conflicted retrievals:** plain URL returned five general awards and pre-opening text; a query-string fetch returned eleven awards and the current deadline. Do not use the older five-award response or earlier twelve-award response as current. |
| SpaceXSI | **MLH-only listing rechecked:** an additional Cursor + Grok Bot raffle appears on MLH. It is absent from the refreshed Devpost list. Confirm participation and how it relates to the category cap before acting. |
| Deadline/category policy | **Rechecked in 2026 overview:** category lock 9 a.m. November 8; final submission/development stop noon; maximum three judged categories. |
| Rules' dates/registration target | **Conflicted:** rules still contain 2025 dates and the older registration link. Preserve the discrepancy; obtain organizer clarification. |
| Overall event-end/ceremony timing | **Needs organizer confirmation:** MLH overview ends 4 p.m.; registration page ends 4:30 p.m.; Devpost schedules winners at 5 p.m. Do not substitute those for the noon submission cutoff. |
| 2026 registration page | **Rechecked independently:** event name and November 7–8, 2026 dates match. This does not establish anyone's registration completion. |
| Sponsor-logo names | **Pending in this Exa refresh:** the extracted sponsor section does not provide reliable logo names. Do not elevate earlier logo descriptions to current evidence. |

Sources fetched through Exa:

- [Refreshed Devpost overview](https://hack-coms-2026.devpost.com/?verify=20261107)
- [Plain overview with older-looking content](https://hack-coms-2026.devpost.com/)
- [Rules](https://hack-coms-2026.devpost.com/rules?verify=20261107)
- [Schedule](https://hack-coms-2026.devpost.com/details/dates?verify=20261107)
- [MLH event](https://www.mlh.com/events/hack-coms-0e)
- [MLH prizes](https://www.mlh.com/events/hack-coms-0e/prizes)
- [2026 registration page](https://events.mlh.com/events/14418-hack-coms-2026)

The query parameter distinguishes the fetched URL; it is not a guarantee that
Exa bypassed every cache. The current six shared categories are corroborated by
an independent official event publisher. Participants/countdowns are not used as
eligibility proof. This ledger stores summaries and links, not full page copies.

## Provider facts refreshed through Exa

| Source | Specific result; remaining boundary |
| --- | --- |
| [Entire CLI](https://raw.githubusercontent.com/entireio/cli/main/README.md) | Existing-repository session capture and checkpoint publication/privacy behavior rechecked. Actual capture and destination remain runtime checks. |
| [Entire Graph](https://raw.githubusercontent.com/entireio/entire-graph/main/README.md) | Python/local analyzer capability rechecked. No measured project savings established. |
| [Entire Brain](https://raw.githubusercontent.com/entireio/entire-brain/main/README.md) | Default setup can process history and install a watcher; extraction may involve a model. Local activation is not proof of retrieval or sync. |
| [Gemini terms](https://aistudio.google.com/docs/terms) | Age/audience, unpaid-input, and regional paid-service restrictions rechecked. Audience decision remains deferred in #33. Original ai.google.dev terms URL timed out; the official AI Studio page succeeded. |
| [Auth0 Django guide](https://developer.auth0.com/resources/guides/web-app/django/basic-authentication) | Login integration via Authlib rechecked. Guide publication is 2024; compatibility with our Django 6.1 runtime is pending. No event-prize claim or account allowance follows from this guide. |
| [Auth0 identity rules](https://auth0.com/docs/manage-users/user-accounts/identify-users) | Tenant-scoped uniqueness rechecked; local issuer/subject mapping remains an engineering decision. |
| [Tiger Data create-service guide](https://www.tigerdata.com/docs/get-started/quickstart/create-service) | PostgreSQL service model and limited free/beta service documented. Actual account plan/credits unverified. |
| [Vultr Python deployment example](https://docs.vultr.com/how-to-deploy-a-fastapi-application-with-gunicorn-and-nginx-on-ubuntu-2404) | App-server/proxy pattern rechecked; example is FastAPI and has inconsistent Ubuntu-version wording. It is not a validated Django deployment recipe. |
| [GoDaddy DNS](https://www.godaddy.com/help/manage-dns-records-680) | DNS-management roles rechecked; qualifying domain offer/registration path remains organizer confirmation. |
| [Solana clusters](https://solana.com/docs/references/clusters) | Devnet/testing context rechecked. Event acceptance of a proposed Devnet demo is not established. |
| [Doppler CLI](https://docs.doppler.com/docs/cli) | Process environment injection rechecked. Team access/config names/runtime delivery remain unverified setup work (#8). |
| [Cloudflare Django](https://developers.cloudflare.com/workers/languages/python/packages/django/) | WSGI backend and adapter transaction limitation rechecked. This is an adapter limitation, not a statement that all D1 operations lack atomicity. |
| [django-cf package](https://raw.githubusercontent.com/cloudflare/workers-py/main/packages/django-cf/README.md) | Production paid-plan requirement rechecked in package documentation; actual account plan and runtime compatibility unverified. |
| [D1 Django example](https://raw.githubusercontent.com/cloudflare/python-workers-examples/main/django-todo-d1/README.md) | Example uses Wrangler SQL migrations rather than Django migrate. Our application schema has not been integrated. |
| [Native D1 batch API](https://developers.cloudflare.com/d1/worker-api/d1-database/) | Transactional batch rollback rechecked. It does not establish transaction support in django-cf. |

Gemini's libraries URL timed out during this Exa refresh. SDK/API/model-version
selection and rate-limit details must be rechecked before implementation; earlier
examples are historical suggestions, not currently validated compatibility.
Unlisted provider details, free-tier marketing, and account-specific allowances
remain pending until their exact sources and account state are checked.

## Repository and runtime boundaries

- `main` at `57fecf5` contains the React/Vite starter and Entire/Graph/Brain guidance.
  Starter files do not establish a working catalog, login, community flow, or API connection.
- Main CI failed for `57fecf5`; [run receipt](https://github.com/Anty120/NextChapter/actions/runs/42416039894).
  The missing dependency-hash regression is #34. Earlier passing CI is historical.
- Entire executable was absent from the parent session's PATH at this check.
  Committed hooks/configuration are observed; capture/Graph/Brain behavior is unverified here.
- Django's checked configuration still uses local SQLite. D1's earlier reachable/empty
  metadata is a historical snapshot; repeat authenticated readback before assuming its state.
- Doppler CLI v3.76.1 was rechecked locally. Doppler selection is a team decision. No credential values or provider account
  configuration were read or changed for this refresh.

Durable source corrections belong in HACKATHON.md / SPONSOR_INTEGRATION.md and the
linked issue bodies. Keep task status/owners on the GitHub Projects board. Never
claim a note in a pending PR is already in main.
