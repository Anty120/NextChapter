"""Offline demo-pack metadata and validation; no database access or downloads."""
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import re
import wave
from datetime import datetime
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError

from catalog.models import Club, MediaItem

DATA_ROOT = Path(__file__).resolve().parent / 'demo_library'
STATIC_ROOT = Path(__file__).resolve().parent / 'static'
REQUIRED_MEDIA = {
    'book-es-01': ('book', 'Spanish'), 'book-en-01': ('book', 'English'),
    'audiobook-es-01': ('audiobook', 'Spanish'), 'audiobook-en-01': ('audiobook', 'English'),
    'song-en-01': ('song', 'English'), 'song-en-02': ('song', 'English'),
}
REQUIRED_CLUBS = {
    'demo-book-club': 'book-es-01', 'demo-audio-club': 'audiobook-es-01',
    'demo-song-club': 'song-en-01',
}
MODEL_FIELDS = ('title', 'creator', 'language', 'format', 'level', 'description',
                'attribution', 'cultural_context', 'difficulty_note', 'published')


class LibraryError(ValueError):
    """The pack is incomplete, unsafe, or inconsistent."""


def _require(condition, message):
    if not condition:
        raise LibraryError(message)


def _read_manifest(name, key):
    try:
        value = json.loads((DATA_ROOT / name).read_text(encoding='utf-8'))
    except (OSError, UnicodeError, ValueError) as exc:
        raise LibraryError(f'{name}: cannot read JSON manifest ({type(exc).__name__})') from exc
    _require(isinstance(value, dict) and type(value.get('schema_version')) is int
             and value['schema_version'] == 1, f'{name}: unsupported schema_version')
    _require(isinstance(value.get(key), list), f'{name}: {key} must be a list')
    return value[key]


def get_media_metadata(slug):
    """Return the unchanged manifest entry, or {} for a non-manifest slug.

    Read each time so an updated pack is visible without stale process caches.
    A broken pack raises LibraryError rather than pretending metadata is absent.
    """
    for item in _read_manifest('media.json', 'items'):
        if isinstance(item, dict) and item.get('slug') == slug:
            return item
    return {}


def normalize_text(text):
    """Normalize line endings/blank lines to the model's paragraph convention."""
    return '\n\n'.join(p.strip() for p in re.split(r'\n\s*\n', text.replace('\r\n', '\n').replace('\r', '\n')) if p.strip())


def asset_path(name, audio=False):
    _require(isinstance(name, str) and name and '\\' not in name,
             'Asset path must be a nonempty relative POSIX path')
    path = PurePosixPath(name)
    _require(not path.is_absolute() and all(part not in ('', '.', '..') for part in name.split('/')),
             f'Unsafe asset path: {name}')
    _require(':' not in name and '?' not in name and '#' not in name, f'Unsafe asset path: {name}')
    if audio:
        _require(name.startswith('catalog/audio/library/'), f'Audio outside library root: {name}')
    root = STATIC_ROOT if audio else DATA_ROOT
    resolved = (root / name).resolve()
    allowed = root.resolve() / 'catalog/audio/library' if audio else root.resolve()
    _require(resolved.is_relative_to(allowed), f'Asset escapes allowed root: {name}')
    _require(resolved.is_file(), f'Missing asset: {name}')
    return resolved


def validate_audio(data, mime, name):
    """Reject mismatched containers and common downloaded HTML/error responses.

    This is a container/signature check, not a claim of human listening or of
    decoding every frame. Asset acquisition separately verifies the recording.
    """
    _require(data and not data.lstrip().lower().startswith((b'<', b'{', b'error', b'not found')),
             f'{name}: HTML/error body or empty audio')
    if mime == 'audio/wav':
        _require(data[:4] == b'RIFF' and data[8:12] == b'WAVE', f'{name}: invalid WAV signature')
        try:
            with wave.open(io.BytesIO(data)) as stream:
                _require(stream.getnframes() > 0 and stream.getframerate() > 0
                         and bool(stream.readframes(1)), f'{name}: empty WAV')
        except (wave.Error, EOFError) as exc:
            raise LibraryError(f'{name}: invalid WAV container') from exc
    elif mime == 'audio/ogg':
        _require(data.startswith(b'OggS') and (b'vorbis' in data[:65536] or b'OpusHead' in data[:65536]),
                 f'{name}: invalid Ogg audio signature')
    elif mime == 'audio/mpeg':
        offset = 0
        if data.startswith(b'ID3'):
            _require(len(data) >= 10 and all(n < 128 for n in data[6:10]), f'{name}: invalid ID3 header')
            offset = 10 + sum(n << shift for n, shift in zip(data[6:10], (21, 14, 7, 0)))
        # Frame sync plus valid MPEG version, layer, bitrate and sample rate.
        header = data[offset:offset + 4]
        _require(len(header) == 4 and header[0] == 255 and header[1] & 224 == 224
                 and header[1] & 24 != 8 and header[1] & 6 != 0
                 and header[2] >> 4 not in (0, 15) and header[2] & 12 != 12,
                 f'{name}: invalid MP3 audio signature')
    else:
        raise LibraryError(f'{name}: unsupported audio MIME')


def _nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def _url(value):
    if not isinstance(value, str):
        return False
    try:
        parsed = urlsplit(value)
        return parsed.scheme in ('http', 'https') and bool(parsed.netloc)
    except ValueError:
        return False


def _sources(item):
    sources = item.get('sources')
    _require(isinstance(sources, list) and sources, f"{item['slug']}: missing provenance")
    components = set()
    for source in sources:
        _require(isinstance(source, dict), f"{item['slug']}: invalid source")
        for field in ('component', 'creator', 'license', 'rights_territory', 'checked_at_utc'):
            _require(_nonempty(source.get(field)), f"{item['slug']}: missing source {field}")
        _require(source['component'] in ('text', 'translation', 'recording', 'composition', 'lyrics', 'cover'),
                 f"{item['slug']}: invalid source component")
        for field in ('source_url', 'license_url'):
            _require(_url(source.get(field)), f"{item['slug']}: invalid {field}")
        _require(isinstance(source.get('modifications'), (str, list)), f"{item['slug']}: missing modifications")
        try:
            checked = datetime.fromisoformat(source['checked_at_utc'].replace('Z', '+00:00'))
            _require(checked.utcoffset() is not None and checked.utcoffset().total_seconds() == 0,
                     f"{item['slug']}: checked_at_utc must be UTC")
        except ValueError as exc:
            raise LibraryError(f"{item['slug']}: invalid checked_at_utc") from exc
        components.add(source['component'])
    _require(bool(components & {'text', 'lyrics'}), f"{item['slug']}: text provenance missing")
    if item['format'] in ('audiobook', 'song'):
        _require('recording' in components, f"{item['slug']}: recording provenance missing")
    if item['format'] == 'song':
        _require({'composition', 'lyrics'} <= components, f"{item['slug']}: composition/lyrics provenance missing")


def load_demo_library():
    """Validate the entire pack before returning model defaults and raw metadata."""
    media, clubs, metadata = {}, {}, {}
    for item in _read_manifest('media.json', 'items'):
        _require(isinstance(item, dict), 'Media entry must be an object')
        slug = item.get('slug')
        _require(_nonempty(slug) and re.fullmatch(r'[-a-zA-Z0-9_]+', slug), 'Invalid media slug')
        _require(slug not in media and slug != 'the-blue-door', f'Duplicate or retired media slug: {slug}')
        for field in MODEL_FIELDS:
            if field != 'published':
                _require(_nonempty(item.get(field)), f'{slug}: missing {field}')
        _require(type(item.get('published')) is bool, f'{slug}: published must be boolean')
        _require(item['format'] in MediaItem.Format.values, f'{slug}: unsupported format')
        _require(item['level'] in dict(MediaItem.LEVELS), f'{slug}: invalid level')
        _sources(item)
        text_name = item.get('text_file')
        text_path = asset_path(text_name)
        try:
            text = normalize_text(text_path.read_text(encoding='utf-8'))
        except UnicodeError as exc:
            raise LibraryError(f'{slug}: text must be UTF-8') from exc
        _require(bool(text), f'{slug}: empty text/transcript')
        defaults = {key: item[key] for key in MODEL_FIELDS}
        defaults.update(text=text, audio_file='')
        required_assets = {text_name}
        if item['format'] in ('audiobook', 'song'):
            name, mime = item.get('audio_file'), item.get('audio_mime')
            audio = asset_path(name, audio=True)
            expected = {'.mp3': 'audio/mpeg', '.ogg': 'audio/ogg', '.wav': 'audio/wav'}
            _require(mime in expected.values() and expected.get(audio.suffix) == mime, f'{slug}: invalid audio MIME/extension')
            duration = item.get('duration_seconds')
            _require(type(duration) in (int, float) and math.isfinite(duration) and duration > 0,
                     f'{slug}: duration_seconds must be positive')
            _require(_nonempty(item.get('performer')) and type(item.get('excerpt')) is bool,
                     f'{slug}: performer/excerpt missing')
            validate_audio(audio.read_bytes(), mime, name)
            defaults['audio_file'] = name
            required_assets.add(name)
        chapters = item.get('chapters', [])
        _require(isinstance(chapters, list) and (item['format'] != 'book' or chapters), f'{slug}: book chapters required')
        previous = -1
        for chapter in chapters:
            _require(isinstance(chapter, dict) and _nonempty(chapter.get('title')), f'{slug}: invalid chapter title')
            index = chapter.get('start_paragraph')
            _require(type(index) is int and previous < index < len(text.split('\n\n')), f'{slug}: invalid chapter index')
            previous = index
        assets = item.get('assets')
        _require(isinstance(assets, list), f'{slug}: assets required')
        seen = set()
        for asset in assets:
            _require(isinstance(asset, dict), f'{slug}: invalid asset entry')
            name = asset.get('path')
            _require(isinstance(name, str) and name not in seen, f'{slug}: duplicate/invalid asset path')
            seen.add(name)
            path = asset_path(name, audio=name.startswith('catalog/audio/'))
            digest = asset.get('sha256')
            _require(isinstance(digest, str) and re.fullmatch('[a-fA-F0-9]{64}', digest), f'{slug}: invalid SHA-256')
            _require(hashlib.sha256(path.read_bytes()).hexdigest() == digest.lower(), f'{slug}: checksum mismatch: {name}')
        _require(required_assets <= seen, f'{slug}: missing asset checksums')
        try:
            MediaItem(slug=slug, **defaults).full_clean(validate_unique=False, validate_constraints=False)
        except ValidationError as exc:
            raise LibraryError(f'{slug}: {exc}') from exc
        media[slug], metadata[slug] = defaults, item
    for slug, (fmt, language) in REQUIRED_MEDIA.items():
        _require(slug in media and media[slug]['published'] and media[slug]['format'] == fmt
                 and media[slug]['language'] == language, f'Required published {language} {fmt} missing: {slug}')
    for club in _read_manifest('clubs.json', 'clubs'):
        _require(isinstance(club, dict), 'Club entry must be an object')
        slug = club.get('slug')
        _require(_nonempty(slug) and slug not in clubs, f'Duplicate/reserved club slug: {slug}')
        for field in ('name', 'language', 'description', 'featured_media_slug'):
            _require(_nonempty(club.get(field)), f'{slug}: missing club {field}')
        target = club['featured_media_slug']
        _require((target in media and media[target]['published'])
                 or (slug == 'the-morning-pages' and target == 'la-panaderia'),
                 f'{slug}: invalid featured media: {target}')
        try:
            Club(**{key: club[key] for key in ('slug', 'name', 'language', 'description')}).full_clean(
                exclude=['featured_media'], validate_unique=False, validate_constraints=False)
        except ValidationError as exc:
            raise LibraryError(f'{slug}: {exc}') from exc
        clubs[slug] = club
    for slug, target in REQUIRED_CLUBS.items():
        _require(slug in clubs and clubs[slug]['featured_media_slug'] == target, f'Required club/target missing: {slug} -> {target}')
    return media, clubs, metadata
