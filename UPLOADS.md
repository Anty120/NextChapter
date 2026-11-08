# Personal books, songs and public review

Sign in and choose **My Library → Upload a file**. Accepted formats are PDF
books and MP3 songs, up to **3 MiB per file** and **30 files or 30 MiB per
account**. Enter title, language and optional author/artist/description, and
confirm permission to upload. Files start private and are not sent to Gemini.
Other users cannot access their metadata, files or positions. `seed_demo`
preserves uploads; they are separate from the bundled catalog.

## Read and listen

PDFs open in the browser's document viewer. If embedding is unavailable, use
Open PDF in a new tab or Download PDF. Enter the page you reached and select
Save page; that page opens next time. The embedded viewer cannot report its
internal page changes to the app, so saving a PDF page is explicit.

MP3 files use native audio controls with no autoplay. Position saves while
listening, on seek and pause, or with Save listening position. Refresh restores
the saved time. Complete MPEG Layer III frames and metadata-duration consistency
are checked. Some unusual tagged exports may need re-exporting as standard MP3.
The maximum duration is two hours.

PDFs must have 1–1000 pages and be unencrypted, without scripts or attachments.
Parsing has scoped resource/structure limits. Validation is structural, not an
antivirus or a copyright determination. PDF uploads use their browser viewer,
without the seeded text reader's word-click Gemini assistance.

## Share for staff review

Choose **Submit for public review** on your upload. Supply author/artist
attribution, license/permission category, optional source link, permission
details, and explicit confirmation that the whole file may be shared publicly.
Staff can preview pending submissions; other readers cannot access them.

Staff with `catalog.change_uploadedmedia` use **Admin → Uploaded media**.
Private uploads are excluded. Review source/permission details and the actual
file before choosing Published or Changes requested. Rejection requires feedback
visible to the uploader; review actor/time are recorded. No bulk auto-publish
action exists. Configure a normal staff/superuser separately if needed:
`python manage.py createsuperuser`. No shared password is seeded.

Approved files appear on a paginated community shelf below the curated catalog
and have public read/listen/download pages. Title/creator, language and format
filters apply; community difficulty is unrated and a selected A1–C2 filter excludes
these files. Broad moderation/blocking (#21) remains deferred.

**Withdraw to private** removes a public listing or pending review, retaining
the owner's copy. Editing metadata also returns the file to private for a fresh
review. Delete requires confirmation and removes the file and position.
Withdrawal cannot recall copies already downloaded while a file was public.

## Setup and storage

```sh
python -m pip install --require-hashes -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Migration `catalog/0002_uploadedmedia_updated.py` adds the upload table.
`pypdf==7.0.0` and `mutagen==1.48.1` are hash-locked direct dependencies.
Existing catalog models and seed inventory remain intact.

Bounded bytes live in Django's configured database: SQLite locally, PostgreSQL/
Neon when configured. No public static file, ephemeral server directory, bucket,
new provider account or object-storage credential is used. Metadata/list queries
defer binary content. Larger files need a separately scoped private object-store
design, rather than raising the cap beyond hosting request/response limits.

A bounded in-memory multipart handler runs before CSRF parsing and caps actual
file bytes and count. Ownership, CSRF, structure and quota checks run server-side.
PostgreSQL account-row locks serialize uploads; SQLite contention produces a
retry message. File endpoints use permission checks, fixed MIME, private/no-store
headers, generated download names and HTTP byte ranges for seeking. Public
endpoints separately require current staff approval on every request.

No production migration/deployment is performed here. #29 stays deferred; its
release owner applies migrations to the intended production database when that
work is explicitly resumed.

## Verification

```sh
python manage.py test tests catalog
python manage.py test scripts.check_uploads_browser
```

Optional Playwright checks need an installed browser; set `ASSISTANCE_BROWSER`
to a local Edge/Chrome executable if required. Fixtures are synthetic PDFs and
an in-memory excerpt of the already credited LibriVox recording. Temporary SQLite
checks cover native PDF rendering/page save, MP3 playback/resume, approval,
public discovery, withdrawal, deletion and 320/390/1024px layouts. No personal
documents/audio are committed or sent to AI. Exact results are in issue #77.
