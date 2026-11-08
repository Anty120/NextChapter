# Bundled library: source and verification record

Checked: 2026-11-08T00:27:34Z (UTC). Sources retrieved through Exa and asset bytes directly from the fixed HTTPS URLs below. Exa responses can be cached; byte downloads were independently hashed during this run. This is source evidence and bounded verification, not worldwide legal clearance.

## Inventory

| Slug | Content | Committed playable duration | Asset bytes |
| --- | --- | ---: | ---: |
| book-es-01 | Marianela | complete book | 628,830 |
| book-en-01 | Alice’s Adventures in Wonderland | complete book | 324,210 |
| audiobook-es-01 | Marianela — Chapter I | 845.06125 | 6,779,920 |
| audiobook-en-01 | Alice — Chapter I | 796.2859375 | 6,383,409 |
| song-en-01 | Daisy Bell | 134.5096875 | 1,215,397 |
| song-en-02 | Auld Lang Syne | 141.5456875 | 1,944,159 |

Two books are complete: Marianela has 22 chapters and 1,264 normalized paragraphs; Alice has 12 chapters and 811 normalized paragraphs. Chapter indexes are zero-based into the exact blank-line-delimited committed text. Both complete Gutenberg downloads, including all notices and the full electronic-edition license, are retained in `text/*.source.txt`; readable files remove front matter and illustration placeholders, join hard-wrapped lines, and keep paragraph boundaries. Audiobook text files contain complete Chapter I of the corresponding book. LibriVox introductions and closing notices are not transcribed. No translation, cover or illustrations are supplied.

## Exact provenance and integrity

The machine-readable per-component sources, creators, rights territories, check times, modifications, and SHA-256 hashes are in `media.json`. Audio files are original upstream bytes: no trimming, transcoding or new arrangement was made. The fixed downloads are:

- **book-es-01**: https://www.gutenberg.org/cache/epub/17340/pg17340.txt; server Content-Type `text/plain; charset=utf-8`; 327,474 bytes; SHA-256 `ec6e5dbd4260583360ab7bd29738505ad5f0dfdf58db3dcbbc401c5ce4fea03f`.
- **book-en-01**: https://www.gutenberg.org/cache/epub/11/pg11.txt; server Content-Type `text/plain; charset=utf-8`; 174,311 bytes; SHA-256 `01b38ea4c710a84bc18d0bd41271a5a1a92b94e97b2812f4dece97d4a694725e`.
- **audiobook-es-01**: https://archive.org/download/marianela_2104_librivox/marianela_01_perezgaldos_64kb.mp3; server Content-Type `audio/mpeg`; 6,769,113 bytes; SHA-256 `e3474b0f3ac0970882e92b63760d668119d2c03a89c82f556813bad71f4e0fc5`.
- **audiobook-en-01**: https://archive.org/download/alices_adventures_1003/alices_adventures_01_carroll_64kb.mp3; server Content-Type `audio/mpeg`; 6,371,811 bytes; SHA-256 `da919b104680c7184a3451ec2cdd65ad0b48ebc0b4eb2ec91620dd9b29e623c6`.
- **song-en-01**: https://upload.wikimedia.org/wikipedia/commons/6/65/Daisy_Bell_sung_by_Edward_M._Favor.ogg; server Content-Type `application/ogg`; 1,214,833 bytes; SHA-256 `26322d595d596470474543b069a53ee23c6ecea0ca18d6093903a00155bdf82b`.
- **song-en-02**: https://upload.wikimedia.org/wikipedia/commons/e/e3/Auld_Lang_Syne.ogg; server Content-Type `application/ogg`; 1,943,425 bytes; SHA-256 `0d277de969ce02959923ec32fd94897a6791cf183fd954198d5e02166e36fb04`.

The Ogg servers return `application/ogg`; the app serves both as `audio/ogg`. MP3 files use `audio/mpeg`. LibriVox catalog times are rounded and may differ slightly from decoded MP3 duration because the original chapter includes spoken notices and encoder padding. The manifest uses fully decoded PCM frame durations, rather than the rounded page values.

### Books and narration

- Marianela text: https://www.gutenberg.org/ebooks/17340 . Author Benito Pérez Galdós, 1878; Gutenberg digitization credited to Chuck Greif. All 22 chapters through the closing date are retained.
- Alice text: https://www.gutenberg.org/ebooks/11 . Author Lewis Carroll, 1865; Gutenberg credits Arthur DiBianca and David Widger, Millennium Fulcrum Edition 3.0. All 12 chapters through the story ending are retained.
- Spanish narration: https://librivox.org/marianela-by-benito-perez-galdos/ ; Maritza Mateo, catalog date 2021-04-03, Chapter I “Perdido”; archive https://archive.org/details/marianela_2104_librivox .
- English narration: https://librivox.org/alices-adventures-in-wonderland-by-lewis-carroll-4/ ; Kara Shallenberg, catalog date 2010-03-18, Chapter I “Down the Rabbit-Hole”; archive https://archive.org/details/alices_adventures_1003 .
- Recording policy: https://librivox.org/pages/public-domain/ identifies recordings as public domain in the USA and explicitly warns that other countries may differ. This page contains older publication-cutoff examples; this pack relies on its recording dedication and each actual source, not those stale examples.

### Songs: recording and words are separate components

- Daisy Bell: https://commons.wikimedia.org/wiki/File:Daisy_Bell_sung_by_Edward_M._Favor.ogg . Harry Dacre words/music, 1892; Edward M. Favor singing in 1894, Edison 1058, UCSB cylinder 10477, original cylinder in John Levin collection. Commons says the spoken introduction was removed upstream. Surface noise remains. Composition and recording have separate public-domain statements on that page.
- Auld Lang Syne: https://commons.wikimedia.org/wiki/File:Auld_Lang_Syne.ogg . Frank C. Stanley, 1910 Indestructible 1267, UCSB cylinder 4410. Upstream click removal credited to Adam Cuerden. This is the original Commons Ogg variant, not a new restoration.
- Daisy historical words source: https://rpo.library.utoronto.ca/content/daisy-bell-or-bicycle-built-two . This University of Toronto edition identifies Harry Dacre and the original 1892 publishers. It is a source link only in this pack.
- Auld Lang Syne original Scots words and context: https://www.scottishpoetrylibrary.org.uk/poem/auld-lang-syne/ . This institutional source describes Burns collecting and reworking an older Scottish song and the Hogmanay custom. The English-language 1910 performance adapts wording; do not describe the linked Scots original as its exact transcript.
- **Full lyrics not bundled for either song.** A content filter blocked the lyric-file write; the coordinator directed credited summaries and links with explicit absence notices. `text/song-*.txt` and the manifest describe these as editorial summaries, not lyrics. This is an acknowledged product limitation requiring human resolution, not a completed lyric-fidelity gate.
- Commons English TimedText for Auld Lang Syne was inspected for source comparison: https://commons.wikimedia.org/wiki/TimedText:Auld_Lang_Syne.ogg.en.srt . No subtitle text, timestamps or modern adaptation is redistributed; no claim of synchronized lyrics is made. Such subtitle contributors/licenses must be assessed separately if later added.

## Executed verification and limits

All four original compressed recordings were fully decoded in one acquisition-only ffmpeg invocation (`-v error -xerror`, four inputs, four mono 16 kHz PCM outputs outside the repository). It exited 0 with no errors. Python stdlib `wave` then read every decoded frame, verified complete frame byte counts and positive RMS. The app, seed and maintenance hash checker do not call ffmpeg. Temporary decoded WAVs, ASR models and tools are not committed.

| Item | Decoded PCM frames at 16 kHz | Seconds | RMS (16-bit) |
| --- | ---: | ---: | ---: |
| song-en-01 | 2,152,155 | 134.5096875 | 2519 |
| song-en-02 | 2,264,731 | 141.5456875 | 1659 |
| audiobook-es-01 | 13,520,980 | 845.06125 | 1388 |
| audiobook-en-01 | 12,740,575 | 796.2859375 | 2795 |

The final Ogg page granule positions independently confirm 134.509705 s and 141.545692 s (resampling explains the sub-sample rounding difference). These are genuine historical vocal recordings according to the exact primary-source descriptions; machine recognition also found nonempty vocal words in both. No human listening was performed, and spectral/RMS measurements alone do not prove intelligibility or singing quality.

Local faster-whisper 1.2.1 / base model, CPU int8, checked original decoded audio. It was an acquisition-only tool in a temporary venv; no remote transcription API received audio. Narration sample windows: English 15–85 s and 710–796 s; Spanish 15–100 s and 740–843 s. A monotonic word-sequence comparison matched 96.8% of 401 recognized English words and 83.0% of 394 recognized Spanish words to the corresponding committed chapter. Both beginning and ending narrative passages matched the proper chapter. These figures measure agreement of sampled machine output, not human-verified WER, alignment, or a claim that every word of the full recording was checked.

Song ASR was deliberately unprompted and weak on the noisy archival audio: Daisy Bell yielded only 44 words in 9 segments, without a reliable title match; Auld Lang Syne yielded 89 words in 9 segments with identifiable song words. This supports vocal content more strongly for Auld Lang Syne and does not establish exact lyric fidelity or verse order for either song. The source performer/song identification is corroborated by the pinned file hash and exact Commons page. Human listening remains a named check; do not pass off generated ASR guesses as lyrics.

HTTP verification: each of the four actual local Django static URLs returned 206 for `Range: bytes=0-63`, the manifest MIME (`audio/mpeg` or `audio/ogg`), Content-Range with the exact file length, and 64 response bytes. The supported-browser host was unavailable in this worker; the coordinator owns actual browser playback/advance/seek/pause/resume checks during integration. Full decode and HTTP success do not claim browser playback or human listening.

A fresh local venv installed locked requirements with `--require-hashes`; with DATABASE_URL unset, local SQLite migrations, `manage.py check`, and the existing 35-test suite passed. The separate worker branches supply manifest-aware seed/player checks; this branch does not claim those integrated checks yet. The schema/asset pack itself passes the frozen field/provenance contract and all local hashes. Maintenance fetch reproducibility is recorded in the PR after execution.

## Maintenance and legacy recording disposition

`python3 scripts/fetch_demo_library.py` verifies local hashes, audio signatures and book chapter boundaries without network. `--fetch` is a deliberate maintenance operation using six fixed sources, 60-second per-request timeouts, a 12 MB response cap, MIME/HTML checks and pinned SHA-256. Source drift fails instead of silently accepting changed material. It retains source notices, restores normalized books and complete first-chapter transcripts, and leaves curated song summaries untouched. It is never a startup dependency. A fresh acquisition must repeat decode/content checks before repinning.

Retire the legacy Microsoft Zira `the-blue-door.wav` from the current distributable/static tree and stop reseeding it as published, while preserving the old database row/ID and user progress as unpublished. New LibriVox recordings replace its role in the demo; they do not resolve Microsoft redistribution permission or establish contributor consent. #12 owns seed behavior; #27 owns binary/regeneration-script retirement and final integration. No changes outside #26 ownership are made here.
