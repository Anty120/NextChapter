# Demo interface and data contract

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
New slugs: `book-es-01`, `book-en-01`, `audiobook-es-01`, `audiobook-en-01`,
`song-en-01`, `song-en-02`. Clubs: `the-morning-pages`, `demo-book-club`,
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
