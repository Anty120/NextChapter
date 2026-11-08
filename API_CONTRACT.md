# Demo interface and data contract

## Personal uploads and public review

`/my-library/` lists the signed-in owner's PDF/MP3 uploads. `/my-library/new/`
accepts GET and CSRF-protected multipart POST (`file`, `title`, `creator`,
`language`, `description`, `permission`). Limits: PDF 3 MiB, MP3 10 MB (10,000,000 bytes); 30 files or 30 MiB/
owner. UUID IDs, server-owned identity and SHA-256 deduplication; bytes persist in
the database. Renamed/empty/truncated/unsupported files and active/encrypted PDFs
are rejected by structural parsers. Parsing is bounded before CSRF reads files.

`/my-library/<uuid>/` is owner-only; its `/file/` endpoint supports GET/HEAD,
single HTTP byte ranges (206/416) and `?download=1`. `/progress/` is POST with
`page` for PDFs or `seconds` for MP3, bounded by the actual file. `/edit/` accepts
metadata GET/POST and withdraws changed submissions. `/delete/` confirms via GET
then requires POST `confirm=delete`; `/withdraw/` is POST and retains a private copy.
Anonymous personal requests redirect to login; another user's ID returns 404.

`/submit/` is owner-only GET/POST, requiring `creator`, `license_name`,
`rights_note`, optional `source_url`, and explicit public `permission`. States:
private → pending → approved/rejected; editing/withdrawal returns to private.
Only staff with change permission can review pending files at
`/my-library/review/<uuid>/[file/]`, using the Django admin queue to decide.
Rejection requires feedback. Staff cannot preview private files in this queue.

Approved-only `/my-library/public/<uuid>/[file/]` pages/files are public; all
other states return 404 there. The catalog's paginated community shelf applies
search/language/format filters; uploads are unrated, so difficulty filters exclude
them. Owner saved positions/review feedback stay private. No automatic Gemini
calls or production/storage-service changes are involved. See [UPLOADS.md](UPLOADS.md).

Run #48 integration, initial base `fb5e15375cf9439291a7528cd93d7cfae8cbd0d6`; main through `16e7d19` incorporated.
Source: `catalog/urls.py`, `catalog/views.py`, `catalog/forms.py`, and
`catalog/models.py`. These are existing Django HTML/form interfaces. Changes need
an explicitly assigned implementation issue and coordination with Anthony.

## Routes

| Method and route | Input | Response and access |
| --- | --- | --- |
| GET `/` | Optional `language`, `format`, `level`, `q` query strings | Public HTML shelf; only published items |
| GET `/media/<id>/` | Published integer media ID | Public HTML story/player; missing/draft item: 404 |
| POST `/media/<id>/progress/` | Form `paragraph` (zero-based integer) for text, or `seconds` (0–86400) for audio | Signed-in user only; saves only that user's progress; normally redirects to media, text with paragraph anchor |
| GET `/clubs/` | None | Public HTML club list |
| GET `/clubs/<id>/` | Optional `page` | Public HTML club and paginated comments |
| POST `/clubs/<id>/membership/` | Form `action=join` or `action=leave` | Signed-in user; redirects to club; invalid action: 400 |
| POST `/clubs/<id>/comments/` | Form `body` (max 2000), optional `spoiler` checkbox | Signed-in club member; success redirects; nonmember: 403; invalid form: HTML 400 |
| GET/POST `/report/media/<id>/` or `/report/comment/<id>/` | POST form `reason` (max 2000) | Signed-in user; GET form; valid POST redirects to target page; invalid form: HTML 400 |
| GET/POST `/accounts/signup/` | Django creation form: `username`, `password1`, `password2` | HTML form; valid submission creates account then redirects to login |
| GET/POST `/accounts/login/` | Django login form: `username`, `password`, optional `next` | Django session login; HTML errors or redirect |
| POST `/accounts/logout/` | CSRF token | Django session logout; follows configured Django logout behavior |

Every state-changing form requires CSRF. Browser requests use same-origin Django
session cookies; the server derives identity from the session. Submitted user IDs,
moderation status and ownership fields are not accepted. Signed-out protected
requests redirect to login, including progress requests asking for JSON.

Examples (browser session and CSRF omitted here; these are payload shapes):

```text
GET /?language=Spanish&format=story&level=A1
POST /clubs/1/membership/      action=join
POST /clubs/1/comments/        body=I+liked+the+market+scene&spoiler=on
POST /media/1/progress/        paragraph=2
POST /media/7/progress/        seconds=12.5
POST /report/media/1/          reason=Please+review+the+credit
```

IDs above are illustrative, not stable seed identifiers. Resolve items by stable
slug when writing fixtures. Language values are stored names (for example
`Spanish`), formats are `story`, `book`, `audiobook`, `song`, and levels are
`A1`, `A2`, `B1`, `B2`, `C1`, `C2`. Levels are editorial estimates.

Progress is the one small JSON response: an authenticated form POST with the exact
header `Accept: application/json` returns `{"saved": true}` on success. Invalid
form values return JSON `{"error": "Invalid position."}` with 400; a missing
required audio position or out-of-range paragraph instead returns plain-text 400.
Consumers must handle those errors and login redirects. There is no general JSON
catalog/community API, React integration, bearer-token auth, or cross-origin API
in the current demo. A future React task must define those interfaces first.

## Data boundaries

- `MediaItem`: unique stable slug; title/creator/language/format/level/description;
  text or transcript; bundled static audio path; attribution; cultural context;
  difficulty note; publication flag. Public queries exclude drafts.
- `Club`: unique slug, name/description/language, optional featured media.
- `Membership`: one row per authenticated user/club; repeated join is safe.
- `Comment`: authenticated author, club, body, spoiler flag, creation time.
  Leaving a club preserves existing comments; posting requires current membership.
- `ReadingProgress`: one row per user/media, paragraph and audio position, update
  time. Only the current user's saved position appears in their page context.
- `Report`: exactly one media/comment target, reporter, reason, review status and
  staff notes. Public forms accept only reason; staff review occurs in Django admin.

`seed_demo` owns six original story slugs, six manifest media slugs and four clubs.
Current slugs: `book-es-01`, `book-en-01`, `audiobook-es-01`, `audiobook-fr-01`,
`song-es-01`, `song-fr-01`. Old English audio is unpublished on reseeding, preserving
IDs and activity. Clubs: `the-morning-pages`, `demo-book-club`,
`demo-audio-club`, `demo-song-club`. `catalog.library.get_media_metadata(slug)`
returns local manifest metadata or `{}` for custom media. Book chapter entries use
zero-based `start_paragraph`; audio metadata includes actual duration, MIME,
performer and excerpt status. MP3 and Ogg static files support HTTP byte ranges.
Songs have editorial summaries and lyric source links, not bundled full lyrics.
`verify_demo` checks the real pack, database and playable static paths without writes.
The legacy `the-blue-door` is no longer created/published; existing rows and progress
remain. The binary and Windows regeneration script are retired. Repeating it preserves
user activity; reviewers must use an isolated local database. Local runs use SQLite with `DATABASE_URL` unset. Hosting is Vercel + Neon Postgres; deployment verification stays #29, and Gemini is deferred.
The migration owner must coordinate schema changes before another agent generates
a migration. API, schema and UI contract changes must land together or have explicit
backward compatibility recorded in the issue.


Songs larger than 3 MiB use session/CSRF-protected POSTs:
`/my-library/song-upload/start/` accepts JSON title/creator/language/description,
`permission: true`, and integer `size` (3 MiB < size <= 10,000,000). It returns
`id`, `chunk_bytes` (1 MiB), `chunk_url`, `finish_url`, `cancel_url`. POST raw
`application/octet-stream` to `chunk_url?offset=N`; returns the acknowledged
`offset`. Exact retries are safe; out-of-order chunks return 409 with `offset`.
POST `finish_url` validates the complete MP3 and returns `{url}` idempotently;
POST `cancel_url` discards the temporary draft. Every draft is owner-only, expires
after 30 minutes, and reserves quota. One draft per account. Expired IDs return
404; deleted completed uploads return 410. Large file GETs require `Range` for
audio bytes (responses capped at 1 MiB). Without Range they show a JavaScript
download page that assembles the original bytes. HEAD reports the full size.
Private/public/staff file permissions are checked on each range request.

## Optional Gemini assistance

`POST /assist/comments/<comment_id>/translate/` accepts JSON
`{"target_language":"en"}`. Supported targets: en/fr/es/de/it/pt/ja/ko/zh/ar/hi.
It requires a signed-in session and CSRF, but not club membership, matching public
comment visibility. The server reads the existing comment (up to 2000 characters);
client-supplied text/model/prompts are ignored. Returns
`{comment_id,target_language,translation}` as plain text data. Missing comments
return 404; other errors follow the standard assistance envelope. The configured
fast lookup model detects source language automatically. Existing quotas apply,
and successful translations are cached by comment content and target language.
The original text remains visible; translation controls/results stay inside
spoiler disclosures. No database migration or new provider key is required.

`POST /assist/explain/` and `POST /assist/pronounce/` require session authentication
and a CSRF token. JSON fields: `media_id`, zero-based `paragraph`, `start`, `end`,
BCP-47 `locale` and `explanation_locale` (default `en`). Offsets count Unicode
codepoints, not JavaScript UTF-16 code units. The server resolves the published
paragraph and accepts 1–1500 selected characters with bounded nearby context
characters. Clients cannot supply arbitrary prompts, models or URLs.

Explain returns `selection`, `language`, `explanation_locale`, `meaning`,
`translation`, `ipa`, `sound_guidance`, `approximation`, `caveat`, `uncertainty`,
and `examples: [{text,note}]`. Pronounce returns playable `audio/wav` bytes.

`POST /assist/practice/` uses multipart with the same reference fields and one
`audio` file: real mono 16-bit PCM WAV, 8–48 kHz, non-silent, at most 60 seconds
and 5 MiB. It returns `transcript`, `reference_match`, `feedback: [{observation,suggestion}]`,
`uncertainty`, and boolean `assessment_supported`. Unsupported assessment clears
observations; dictation agreement is not a pronunciation grade.

Errors use `{error: {code,message}}`, statuses 400/401/403/413/429/502/503. Responses
are private/no-store, including speech analysis. Missing configuration returns 503.
Features remain optional and credential-free core flows keep working. See
[ASSISTANCE.md](ASSISTANCE.md) for flags, deployment cache and data handling.

`POST /assist/lookup/` uses the same reference, capped at 300 characters, and
returns concise translation/meaning/IPA/approximation in the explain response
shape. `POST /assist/sentence/` accepts up to 1500 characters for concise sentence
help. Both use `GEMINI_LOOKUP_MODEL` (fallback: text model).
`POST /assist/phonetics/` accepts the sentence reference and returns
`words: [{start,end,text,ipa,sound}]`, codepoint offsets relative to that selection,
plus a notice. Authentication, CSRF and quota handling match explain.

`GET/POST /media/<pk>/quiz/` provides optional curated comprehension questions for
the two bundled books. GET does not disclose answer keys; CSRF-protected POST
validates all answers and grades on the server. Results are not stored and do not
affect a learner's level. Drafts, nonbooks and books without a quiz return 404.
