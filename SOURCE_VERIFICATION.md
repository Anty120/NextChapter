# Project knowledge: verification ledger

## 10 MB songs — checked 2026-11-08 06:29 UTC

- Primary source: [Vercel function limits](https://vercel.com/docs/functions/limitations).
  Official web fetch confirmed a 4.5 MB request/response payload cap; Exa is not
  available in this session. Cached responses remain possible. This is a provider
  limit, not evidence about our deployed account or deployment behavior.
- Songs now accept up to 10,000,000 bytes; PDFs remain 3 MiB. Larger songs use
  authenticated 1 MiB upload chunks and bounded range responses. Downloads are
  assembled in the browser. No streaming exemption is assumed for Django WSGI.
- Separate local runtime evidence: Edge uploaded an exact 10,000,000-byte MP3;
  maximum upload request body was 1,048,576 bytes. Native playback, distant seek,
  refresh/resume and byte-identical download passed at mobile widths 320/390.
  Production transport, migrations and persistence require separate verification;
  deployment issue #29 remains deferred.

## PDF/MP3 upload implementation — checked 2026-11-08 05:15 UTC

Exa is unavailable. Official documentation was read through web open/search;
PyPI package metadata and hash-locked packages were fetched directly. Search
snippets can be stale: the cached pypdf security snippet said 6.21.4, while the
opened stable page and actual package metadata identified 7.0.0. Runtime imports
and real PDF/MP3 browser checks separately verify the selected implementation.

| Primary source | Claim / result |
| --- | --- |
| https://vercel.com/docs/functions/limitations | Current page documents a 4.5 MB request/response payload limit. The app caps file bytes at 3 MiB plus bounded metadata and stores bytes in the existing database; no new blob service or deployment is configured. |
| https://docs.djangoproject.com/en/6.1/ref/files/uploads/ | Custom upload handlers can bound chunks and abort uploads before normal file storage. Implemented bounded in-memory handling before CSRF parsing; browser MIME is not trusted. |
| https://pypdf.readthedocs.io/en/stable/user/security.html | Scoped parsing limits use `apply_configuration`; actual 7.0.0 package supports these limits. |
| https://pypdf.readthedocs.io/en/stable/modules/configuration.html | Reviewed public limit names for stream size/decompression, page-tree depth/entries and container counts. Applied bounded values while structurally reading PDFs and rejecting active features/attachments. No OCR or arbitrary script execution. |
| https://mutagen.readthedocs.io/en/latest/api/mp3.html | MP3 parsing exposes stream layer/sample rate/duration. Pinned 1.48.1; actual in-memory LibriVox-derived test MP3 parsed and played. Added complete-frame scanning and metadata-duration consistency rejection for truncation. |
| https://pypi.org/pypi/pypdf/json | 7.0.0, Python >=3.10; installed from the hash-locked requirements. No optional crypto/OCR extras selected. |
| https://pypi.org/pypi/mutagen/json | 1.48.1, Python >=3.10; no extra runtime dependencies. Hash-locked and tested. |

Tests use synthetic PDFs and a temporary excerpt of the existing credited
LibriVox MP3; no personal content is committed or sent to AI. Owner explicitly
selected private uploads plus public staff-review submissions. This bounded
review workflow does not reactivate deferred #21/#29/#64. Production persistence
requires applying the new migration to the intended database during an authorized
release; no live deployment or production write is claimed here.

## Motion UI and GitHub completion audit — 2026-11-08 04:27 UTC

Exa tools are unavailable in this session. Official Motion documentation was
opened through web search/open; package metadata and tarball were fetched directly
from the npm registry. Page responses may be cached. GitHub issues/board/PRs and
remote-main ancestry were read through authenticated `gh`/Git, separately from
local runtime tests. No deployment, provider account or secrets changes followed.

| Primary source | Claim / checked result |
| --- | --- |
| https://motion.dev/docs/animate | Motion's browser animation API supports easing and spring transitions. Local integration uses transform/opacity animation, not a React framework migration. |
| https://motion.dev/docs/spring | Reviewed spring configuration. UI uses restrained stiffness/damping/mass for hover, press and a short heading entrance. Runtime behavior is separately browser-tested. |
| https://motion.dev/docs/quick-start | Official script-tag distribution is supported. Runtime scripts are bundled locally, with a no-library/no-JS fallback; no external CDN is contacted by the app. |
| https://registry.npmjs.org/motion/14.10.1 | Verified package version, MIT license and published SHA-512 tarball integrity. Extracted only the named browser build and license, with no dependency install or lifecycle script. |
| https://registry.npmjs.org/motion/-/motion-14.10.1.tgz | Downloaded tarball matched registry integrity. Unmodified `dist/motion.js`: 183,604 bytes; SHA-256 `b39d6cdb97506ae8c00da5221ad23bb3799845b64bf58b8e19c297d81211a916`. License and machine-readable provenance retained under `catalog/static/catalog/vendor/motion/`. |

The remote project audit closed completed #3/#4/#5/#10/#28/#61/#62/#71/#72 and
retired #66 as not planned because the English recordings were superseded.
Deployment safety (#29), human speech evaluation (#64/#60), wider moderation
(#21), teammate access (#8/#9) and ongoing independent redesign (#70) remain open.
See `docs/reviews/project-audit-motion.md` and each issue's completion note for
the evidence and limits; local-main-only work is not a remote deployment receipt.

## Reader speed and non-English recordings — checked 2026-11-08 02:29 UTC

Exa is unavailable in this session. Official web search/page reads and direct
HTTPS downloads were used as fallback; cached-page freshness is not guaranteed.
These claims concern provider capabilities/content, not event prizes.

| Source | Claim / status |
| --- | --- |
| https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite | Official low-latency model description. Actual account generateContent with structured JSON succeeded; new adapter cold 0.876 s, cached <1 ms for public French moi. Earlier full explanation sample 12.307 s. Individual samples, no SLA. |
| https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash-lite | Documentation exists, but actual account request returned configuration HTTP 503 through our adapter. Not selected; source/runtime conflict preserved. |
| https://ai.google.dev/gemini-api/docs/optimization | Reviewed latency guidance. Implemented smaller output, separate lookup model and reference caching; no priority-tier or billing change. |
| https://commons.wikimedia.org/wiki/File:Attaignant_Tourdion_Sung_by_the_dwsChorale.ogg | French sung performance by dwsChorale/Dwsolo; 2006, CC BY-SA 3.0 confirmed by page and live imageinfo metadata. Original Ogg downloaded, 1,446,765 bytes, SHA-256 in media.json. |
| https://commons.wikimedia.org/wiki/File:Las_Mananitas.ogg | Spanish sung opening of Mexican birthday song; Elisa vocals / Kenmayer mix, Educational Options Inc.; CC BY-SA 3.0 confirmed in live imageinfo metadata. Original Ogg downloaded, 447,841 bytes. It is an excerpt. |

French short-story narration was generated from project-owned public text with
the already configured Gemini TTS model, saved as a local WAV and explicitly
credited as synthetic. Commons recording license notices are retained separately
from MIT source code. Runtime evidence is recorded in the learning-flow review.

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

## Run #48 bundled library and Vercel build evidence

- **2026-11-08T00:27:34Z — #26 evidence:** Six-item Gutenberg/LibriVox/Commons pack
  independently downloaded, hashed, fully audio-decoded and source-checked; see
  [catalog/demo_library/SOURCES.md](catalog/demo_library/SOURCES.md) for each primary
  source URL, exact component license, modifications and check time, and
  [PR #59](https://github.com/Anty120/NextChapter/pull/59) for executed acquisition checks.
  USA scope retained; full lyrics absent and human listening pending. This is an
  imported worker verification record, not a claim that the integrator repeated
  source acquisition or that public-domain status applies in every jurisdiction.
- **2026-11-08 00:28 UTC — #49 source record:** Checked through Exa and live HTTPS
  (cache still possible). Primary sources:
  https://vercel.com/docs/frameworks/full-stack/django (Django entry resolution and CDN collectstatic),
  https://vercel.com/docs/functions/runtimes/python (Python 3.12/top-level WSGI callable),
  https://vercel.com/docs/project-configuration/vercel-json (buildCommand/functions),
  https://vercel.com/docs/cli/build (local output and --yes environment-pull behavior).
  Claim status: supported by fetched primary docs and local output; live deployment
  unverified. Evidence: [#49 comment 6715073527](https://github.com/Anty120/NextChapter/issues/49#issuecomment-6715073527),
  PR #57 / `9d89773`: Vercel CLI 58.5.1 build exited 0 with Python 3.12/uv 0.13.7,
  Build Output API v3, django.func Python 3.12, generated WSGI launcher and CDN assets.
  This macOS fixture build does not verify remote environment or portable Linux output.
  No deployment, remote environment mutation, Git connection, cloud migrate or seed
  was performed. These are the #49 worker's bounded results, retained separately from
  the integration's local runtime checks. Deployment/persistence remains #29.

## Gemini implementation refresh — 2026-11-08 01:02 UTC / November 7 EST

Exa was unavailable in this session. Official Google docs were fetched directly
at 00:31 UTC after the web renderer rejected Markdown responses. Current API
fields were rechecked with official-domain web search at 01:00–01:02 UTC. Cached
documentation remains possible; account/model transport has separate live proof.

| Primary source | Supported claim / boundary |
| --- | --- |
| [Audio input](https://ai.google.dev/gemini-api/docs/audio) | Audio input/transcription exists; it does not establish calibrated phonetic assessment. |
| [TTS](https://ai.google.dev/gemini-api/docs/speech-generation) | Speech generation and French support documented; current examples emphasize Interactions. Legacy generateContent was independently live-tested. |
| [GenerateContent schema](https://ai.google.dev/api/generate-content?hl=en) | Indexed reference documents inlineData, speechConfig.languageCode and responseSchema. Direct reference redirects conflicted with accessible indexed content; real requests resolve compatibility for the tested models only. |
| [Structured output](https://ai.google.dev/gemini-api/docs/structured-output) | Structured JSON output; application validates shape/length separately. |
| [Terms](https://ai.google.dev/gemini-api/terms) | Paid/unpaid data handling differs. Owner confirmed actual personal-voice configuration; no independent billing/region audit or billing changes were performed. |
| [Django cache](https://docs.djangoproject.com/en/6.0/topics/cache/) | RedisCache requires redis-py; shared atomic quotas need an appropriate backend. Actual deployed Redis remains unverified. |
| [Redis package](https://pypi.org/project/redis/8.1.0/) | Official PyPI metadata provided version 8.1.0 and artifact SHA-256 hashes for the optional production cache lock. |

Runtime: authenticated Gemini model listing advertised generateContent for the
configured 3.8 text/TTS models. Live French moi explanation returned /mwa/,
maison and Spanish libro contextual help succeeded. A speech-script correction
removed spoken prose instructions: the corrected moi WAV lasted 1.2 seconds and
audio dictation returned Moi. This is a content/transport smoke, not an independent
pronunciation benchmark. The dev Doppler model IDs/feature flags were configured;
keys were never printed or committed. See [Gemini acceptance](docs/reviews/gemini-acceptance.md)
for combined app checks and unresolved quality criteria. No main merge or deployment.
