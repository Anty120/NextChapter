"""Read-only verification of the bundled pack, database and static resolution."""
import hashlib
from urllib.parse import urlsplit

from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.management.base import BaseCommand, CommandError

from catalog.library import LibraryError, load_demo_library, validate_audio
from catalog.models import Club, MediaItem

ORIGINAL_STORIES = ('la-panaderia', 'el-mercado', 'el-huerto', 'el-tren', 'la-carta', 'le-livre-jaune')


def check_playable(item):
    """Check both the finder source and the URL's collected/hashed asset.

    Before collectstatic the finder suffices. Once a manifest storage maps the
    URL, that exact mapped file must exist and match the committed checksum.
    """
    name = item['audio_file']
    digest = next(asset['sha256'].lower() for asset in item['assets'] if asset['path'] == name)
    found = finders.find(name)
    available = False
    if found:
        from pathlib import Path
        data = Path(found).read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise LibraryError(f'{name}: static finder checksum mismatch')
        validate_audio(data, item['audio_mime'], name)
        available = True
    # Manifest storage must resolve the same path used by the rendered player.
    if hasattr(staticfiles_storage, 'stored_name'):
        try:
            stored = staticfiles_storage.stored_name(name)
            url = staticfiles_storage.url(name, force=True)
        except (ValueError, OSError) as exc:
            raise LibraryError(f'{name}: collectstatic manifest cannot resolve playable URL') from exc
        if not urlsplit(url).path or not staticfiles_storage.exists(stored):
            raise LibraryError(f'{name}: collected playable asset missing')
        with staticfiles_storage.open(stored, 'rb') as stream:
            data = stream.read()
        if hashlib.sha256(data).hexdigest() != digest:
            raise LibraryError(f'{name}: collected checksum mismatch')
        validate_audio(data, item['audio_mime'], stored)
        available = True
    elif staticfiles_storage.exists(name):
        with staticfiles_storage.open(name, 'rb') as stream:
            data = stream.read()
        if hashlib.sha256(data).hexdigest() != digest:
            raise LibraryError(f'{name}: collected checksum mismatch')
        available = True
    if not available:
        raise LibraryError(f'{name}: no playable static finder/storage path')


class Command(BaseCommand):
    help = 'Verify demo manifests, assets, seeded records, clubs and playable static paths without writing data.'

    def handle(self, *args, **options):
        try:
            media, clubs, metadata = load_demo_library()
            for slug, defaults in media.items():
                item = MediaItem.objects.filter(slug=slug).first()
                if item is None:
                    raise LibraryError(f'{slug}: missing database row; run seed_demo')
                for field, value in defaults.items():
                    if getattr(item, field) != value:
                        raise LibraryError(f'{slug}: database {field} differs from manifest; run seed_demo')
                if item.is_audio:
                    check_playable(metadata[slug])
                detail = f"{metadata[slug]['duration_seconds']}s, {metadata[slug]['audio_mime']}" if item.is_audio else f'{len(item.paragraphs)} paragraphs'
                self.stdout.write(f'{slug}: {item.format}, {item.language}, {item.level}, {detail}, pk={item.pk}')
            for slug in ORIGINAL_STORIES:
                story = MediaItem.objects.filter(slug=slug, format='story', published=True).first()
                if story is None or not story.text.strip() or not story.attribution.strip():
                    raise LibraryError(f'{slug}: original published story missing or unusable')
            for slug, expected in clubs.items():
                club = Club.objects.select_related('featured_media').filter(slug=slug).first()
                if (club is None or club.featured_media is None
                        or club.featured_media.slug != expected['featured_media_slug']
                        or not club.featured_media.published
                        or any(getattr(club, key) != expected[key] for key in ('name', 'language', 'description'))):
                    raise LibraryError(f'{slug}: club missing or differs from manifest; run seed_demo')
                self.stdout.write(f'{slug}: club -> {club.featured_media.slug}, pk={club.pk}')
            if not Club.objects.filter(slug='the-morning-pages', featured_media__slug='la-panaderia',
                                       featured_media__published=True).exists():
                raise LibraryError('the-morning-pages: original club/featured story missing')
            if MediaItem.objects.filter(slug='the-blue-door', published=True).exists():
                raise LibraryError('the-blue-door: unsupported legacy narration is still published')
        except (LibraryError, OSError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(
            f'Verified {len(media)} manifest media + 6 original stories; '
            f'{len(clubs) + 1} demo clubs; all required assets and playable paths valid.'))
