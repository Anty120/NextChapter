#!/usr/bin/env python3
"""Maintenance-only, pinned-source restoration; ordinary app startup never calls this.

Run without flags to verify every committed asset hash. --fetch downloads the six
fixed upstream files and deterministically restores books/chapter transcripts.
Song summaries are curated locally and are never silently regenerated.
No decoder, provider credential or third-party Python dependency is needed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'catalog/demo_library'
STATIC = ROOT / 'catalog/static'
# Pinned bytes checked 2026-11-08 UTC. Upstream changes require a new source review.
DOWNLOADS = {
    'text/book-es-01.source.txt': ('https://www.gutenberg.org/cache/epub/17340/pg17340.txt', 'ec6e5dbd4260583360ab7bd29738505ad5f0dfdf58db3dcbbc401c5ce4fea03f'),
    'text/book-en-01.source.txt': ('https://www.gutenberg.org/cache/epub/11/pg11.txt', '01b38ea4c710a84bc18d0bd41271a5a1a92b94e97b2812f4dece97d4a694725e'),
    'catalog/audio/library/audiobook-es-01.mp3': ('https://archive.org/download/marianela_2104_librivox/marianela_01_perezgaldos_64kb.mp3', 'e3474b0f3ac0970882e92b63760d668119d2c03a89c82f556813bad71f4e0fc5'),
    'catalog/audio/library/audiobook-en-01.mp3': ('https://archive.org/download/alices_adventures_1003/alices_adventures_01_carroll_64kb.mp3', 'da919b104680c7184a3451ec2cdd65ad0b48ebc0b4eb2ec91620dd9b29e623c6'),
    'catalog/audio/library/song-en-01.ogg': ('https://upload.wikimedia.org/wikipedia/commons/6/65/Daisy_Bell_sung_by_Edward_M._Favor.ogg', '26322d595d596470474543b069a53ee23c6ecea0ca18d6093903a00155bdf82b'),
    'catalog/audio/library/song-en-02.ogg': ('https://upload.wikimedia.org/wikipedia/commons/e/e3/Auld_Lang_Syne.ogg', '0d277de969ce02959923ec32fd94897a6791cf183fd954198d5e02166e36fb04'),
}


def asset_path(relative):
    base = STATIC if relative.startswith('catalog/audio/library/') else DATA
    candidate = base / relative
    if candidate.is_symlink() or not candidate.resolve().is_relative_to(base.resolve()):
        raise ValueError(f'Unsafe asset path: {relative}')
    return candidate


def normalize_book(raw, language):
    """Keep chapter text, join hard-wrapped lines, retain blank-line paragraphs."""
    body = re.split(r'\*\*\* START OF THE PROJECT GUTENBERG EBOOK .*?\*\*\*', raw, maxsplit=1)[1]
    body = re.split(r'\*\*\* END OF THE PROJECT GUTENBERG EBOOK .*?\*\*\*', body, maxsplit=1)[0]
    pattern = r'^-[IVX]+-\s*$' if language == 'es' else r'^CHAPTER [IVX]+\.\s*$'
    first = re.search(pattern, body, re.M)
    if first is None:
        raise ValueError('No chapter heading')
    body = body[first.start():].strip()
    # Illustrations are not bundled; no artwork rights are implied.
    body = re.sub(r'\[Illustration[^\]]*\]', '', body)
    paragraphs = [' '.join(p.split()) for p in re.split(r'\n\s*\n', body) if p.strip()]
    chapters = []
    heading = r'-[IVX]+-' if language == 'es' else r'CHAPTER [IVX]+\..*'
    for i, paragraph in enumerate(paragraphs):
        if re.fullmatch(heading, paragraph):
            title = paragraph
            if language == 'es':
                title += ' ' + paragraphs[i + 1]
            chapters.append({'title': title, 'start_paragraph': i})
    expected = 22 if language == 'es' else 12
    if len(chapters) != expected:
        raise ValueError(f'Expected {expected} chapters, got {len(chapters)}')
    return paragraphs, chapters


def restore_text():
    for language in ('es', 'en'):
        raw = asset_path(f'text/book-{language}-01.source.txt').read_text(encoding='utf-8-sig')
        paragraphs, chapters = normalize_book(raw, language)
        asset_path(f'text/book-{language}-01.txt').write_text('\n\n'.join(paragraphs) + '\n', encoding='utf-8', newline='\n')
        chapter_one = paragraphs[:chapters[1]['start_paragraph']]
        asset_path(f'text/audiobook-{language}-01.txt').write_text('\n\n'.join(chapter_one) + '\n', encoding='utf-8', newline='\n')


def download():
    for relative, (url, expected) in DOWNLOADS.items():
        request = urllib.request.Request(url, headers={'User-Agent': 'NextChapter-demo-maintenance/1.0'})
        with urllib.request.urlopen(request, timeout=60) as response:
            if response.status != 200:
                raise ValueError(f'Unexpected HTTP status for {relative}')
            mime = response.headers.get_content_type()
            allowed = {'audio/mpeg'} if relative.endswith('.mp3') else {'audio/ogg', 'application/ogg'} if relative.endswith('.ogg') else {'text/plain'}
            if mime not in allowed:
                raise ValueError(f'Unexpected MIME {mime} for {relative}')
            content = response.read(12_000_001)
        if not content or len(content) > 12_000_000 or b'<html' in content[:512].lower():
            raise ValueError(f'Empty, oversized or HTML response for {relative}')
        if hashlib.sha256(content).hexdigest() != expected:
            raise ValueError(f'Upstream bytes changed for {relative}; review provenance before repinning')
        path = asset_path(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    restore_text()


def verify():
    manifest = json.loads((DATA / 'media.json').read_text(encoding='utf-8'))
    seen = set()
    total = 0
    for item in manifest['items']:
        for asset in item['assets']:
            relative = asset['path']
            content = asset_path(relative).read_bytes()
            if not content or hashlib.sha256(content).hexdigest() != asset['sha256']:
                raise ValueError(f'Missing, empty or changed asset: {relative}')
            if relative.endswith('.ogg') and not (content.startswith(b'OggS') and b'vorbis' in content[:128]):
                raise ValueError(f'Invalid Ogg/Vorbis: {relative}')
            if relative.endswith('.mp3') and not (content.startswith(b'ID3') or content[0] == 255 and content[1] & 224 == 224):
                raise ValueError(f'Invalid MPEG audio: {relative}')
            if relative not in seen:
                total += len(content)
                seen.add(relative)
        if item['format'] == 'book':
            language = 'es' if item['language'] == 'Spanish' else 'en'
            raw = asset_path(f'text/{item["slug"]}.source.txt').read_text(encoding='utf-8-sig')
            paragraphs, chapters = normalize_book(raw, language)
            if chapters != item['chapters'] or asset_path(item['text_file']).read_text(encoding='utf-8') != '\n\n'.join(paragraphs) + '\n':
                raise ValueError(f'Book chapter boundaries changed: {item["slug"]}')
    print(f'PASS: {len(manifest["items"])} items, {len(seen)} unique assets, {total:,} bytes; hashes, audio signatures, full text and chapter indexes verified')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch', action='store_true', help='Restore pinned upstream assets (maintenance network operation)')
    args = parser.parse_args()
    if args.fetch:
        download()
    verify()
