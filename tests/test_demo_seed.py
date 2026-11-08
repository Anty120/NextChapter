"""Small isolated packs exercise the production contract without network/media tools."""
import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
import wave

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from catalog import library
from catalog.models import Club, Comment, MediaItem, Membership, ReadingProgress, Report


class DemoSeedTests(TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / 'demo_library'
        self.static = self.root / 'static'
        self.data.mkdir()
        self.static.mkdir()
        self.enterContext(patch.object(library, 'DATA_ROOT', self.data))
        self.enterContext(patch.object(library, 'STATIC_ROOT', self.static))
        self.enterContext(override_settings(STATICFILES_DIRS=[self.static], STATIC_ROOT=self.root / 'collected'))
        self.items = []
        for slug, (fmt, language) in library.REQUIRED_MEDIA.items():
            text_name = f'text/{slug}.txt'
            self.write_asset(text_name, b'First paragraph.\r\n\r\nSecond paragraph.\r\n\r\nThird paragraph.')
            item = dict(slug=slug, title=slug, creator='Fixture author', language=language,
                        format=fmt, level='B2', description='Fixture description', text_file=text_name,
                        attribution='Fixture credits', cultural_context='Fixture context',
                        difficulty_note='Editorial estimate', published=True,
                        sources=[self.source('text')], assets=[self.asset(text_name)])
            if fmt == 'book':
                item['chapters'] = [{'title': 'One', 'start_paragraph': 0}, {'title': 'Two', 'start_paragraph': 2}]
            if fmt in ('audiobook', 'song'):
                name = f'catalog/audio/library/{slug}.wav'
                stream = io.BytesIO()
                with wave.open(stream, 'wb') as audio:
                    audio.setparams((1, 2, 8000, 0, 'NONE', 'not compressed'))
                    audio.writeframes(b'\x01\x02' * 800)
                self.write_asset(name, stream.getvalue())
                item.update(audio_file=name, audio_mime='audio/wav', duration_seconds=0.1,
                            performer='Fixture performer', excerpt=fmt == 'audiobook')
                item['assets'].append(self.asset(name))
                item['sources'].append(self.source('recording'))
                if fmt == 'song':
                    item['sources'].extend([self.source('composition'), self.source('lyrics')])
            self.items.append(item)
        self.clubs = [dict(slug=slug, name=slug, language='Spanish' if 'book' in slug or 'audio' in slug else 'English',
                           description='Welcome! Share a favorite passage.', featured_media_slug=target)
                      for slug, target in library.REQUIRED_CLUBS.items()]
        self.save()

    def source(self, component):
        return dict(component=component, creator='Fixture author', source_url='https://example.org/source',
                    license='Fixture permission', license_url='https://example.org/license', rights_territory='USA',
                    checked_at_utc='2026-11-07T23:00:00Z', modifications='None')

    def write_asset(self, name, data):
        path = (self.static if name.startswith('catalog/audio/') else self.data) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def asset(self, name):
        path = (self.static if name.startswith('catalog/audio/') else self.data) / name
        return dict(path=name, sha256=hashlib.sha256(path.read_bytes()).hexdigest())

    def save(self):
        (self.data / 'media.json').write_text(json.dumps({'schema_version': 1, 'items': self.items}))
        (self.data / 'clubs.json').write_text(json.dumps({'schema_version': 1, 'clubs': self.clubs}))

    def command(self, name):
        out = io.StringIO()
        call_command(name, stdout=out)
        return out.getvalue()

    def test_idempotent_seed_verify_preserves_all_user_activity_and_ids(self):
        self.command('seed_demo')
        user = get_user_model().objects.create_user('existing', password='fixture-password')
        password = user.password
        story = MediaItem.objects.get(slug='la-panaderia')
        legacy = MediaItem.objects.create(slug='the-blue-door', title='Legacy recording', creator='Legacy',
                                         language='English', format='audiobook', level='A1',
                                         text='Original transcript', audio_file='catalog/audio/the-blue-door.wav', published=True)
        custom = MediaItem.objects.create(slug='custom-story', title='My story', creator='Me',
                                         language='English', format='story', level='A2', text='My own text', published=True)
        club = Club.objects.get(slug='the-morning-pages')
        custom_club = Club.objects.create(slug='custom-club', name='Custom', featured_media=custom)
        Membership.objects.create(user=user, club=club)
        comment = Comment.objects.create(user=user, club=club, body='Keep this comment')
        Report.objects.create(reporter=user, comment=comment, reason='Keep report')
        ReadingProgress.objects.create(user=user, media=story, paragraph=2)
        ReadingProgress.objects.create(user=user, media=legacy, seconds=33)
        ReadingProgress.objects.create(user=user, media=MediaItem.objects.get(slug='audiobook-en-01'), seconds=0.05)
        ids = dict(MediaItem.objects.values_list('slug', 'pk'))
        clubs = dict(Club.objects.values_list('slug', 'pk'))
        for _ in range(2):
            self.command('seed_demo')
            self.assertIn('Verified 6 manifest media + 6 original stories; 4 demo clubs', self.command('verify_demo'))
            self.assertEqual(dict(MediaItem.objects.values_list('slug', 'pk')), ids)
            self.assertEqual(dict(Club.objects.values_list('slug', 'pk')), clubs)
        user.refresh_from_db()
        legacy.refresh_from_db()
        custom.refresh_from_db()
        self.assertEqual(user.password, password)
        self.assertTrue(user.check_password('fixture-password'))
        self.assertFalse(legacy.published)
        self.assertEqual(legacy.text, 'Original transcript')
        self.assertEqual(legacy.audio_file, 'catalog/audio/the-blue-door.wav')
        self.assertEqual(custom.text, 'My own text')
        self.assertTrue(Club.objects.filter(pk=custom_club.pk).exists())
        self.assertEqual((Membership.objects.count(), Comment.objects.count(), Report.objects.count()), (1, 1, 1))
        self.assertEqual(list(ReadingProgress.objects.order_by('pk').values_list('paragraph', 'seconds')),
                         [(2, 0), (0, 33), (0, 0.05)])
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_helper_returns_exact_contract_keys_and_no_db_queries(self):
        for item in self.items:
            with self.assertNumQueries(0):
                metadata = library.get_media_metadata(item['slug'])
            self.assertEqual(metadata, item)
            for key in ('chapters', 'audio_mime', 'duration_seconds', 'performer', 'excerpt', 'sources'):
                if key in item:
                    self.assertEqual(metadata[key], item[key])
        with self.assertNumQueries(0):
            self.assertEqual(library.get_media_metadata('custom-story'), {})

    def test_bad_pack_never_writes_and_can_be_fixed(self):
        original = copy.deepcopy(self.items)
        original_clubs = copy.deepcopy(self.clubs)
        cases = [
            ('duplicate', lambda: self.items.append(copy.deepcopy(self.items[0]))),
            ('bad target', lambda: self.clubs[0].update(featured_media_slug='missing')),
            ('hash', lambda: self.items[0]['assets'][0].update(sha256='0' * 64)),
            ('missing file', lambda: self.items[0].update(text_file='text/missing.txt')),
            ('MIME', lambda: self.items[2].update(audio_mime='text/html')),
            ('format', lambda: self.items[0].update(format='video')),
            ('level', lambda: self.items[0].update(level='A0')),
            ('credits', lambda: self.items[0].update(attribution='')),
            ('rights', lambda: self.items[0]['sources'][0].update(rights_territory='')),
            ('chapter', lambda: self.items[0]['chapters'][1].update(start_paragraph=3)),
            ('negative chapter', lambda: self.items[0]['chapters'][0].update(start_paragraph=-1)),
            ('bool chapter', lambda: self.items[0]['chapters'][0].update(start_paragraph=False)),
            ('no chapters', lambda: self.items[0].pop('chapters')),
            ('no transcript', lambda: self.items[2].update(text_file='text/missing.txt')),
            ('no audio', lambda: self.items[2].update(audio_file='catalog/audio/library/missing.wav')),
            ('unpublished', lambda: self.items[0].update(published=False)),
            ('traversal', lambda: self.items[0].update(text_file='../escape.txt')),
            ('absolute', lambda: self.items[0].update(text_file=str(self.data / 'text/book-es-01.txt'))),
            ('remote audio', lambda: self.items[2].update(audio_file='https://example.org/audio.wav')),
            ('no hashes', lambda: self.items[0].update(assets=[])),
            ('no provenance', lambda: self.items[0].update(sources=[])),
            ('bad duration', lambda: self.items[2].update(duration_seconds=float('nan'))),
            ('wrong club mapping', lambda: self.clubs[0].update(featured_media_slug='book-en-01')),
        ]
        self.command('seed_demo')
        snapshot = list(MediaItem.objects.values())
        club_snapshot = list(Club.objects.values())
        for label, mutate in cases:
            with self.subTest(label=label):
                self.items, self.clubs = copy.deepcopy(original), copy.deepcopy(original_clubs)
                # Would update an earlier row if validation wrote incrementally.
                self.items[0]['title'] = 'Must not be persisted'
                mutate()
                self.save()
                with self.assertRaises(CommandError):
                    self.command('seed_demo')
                self.assertEqual(list(MediaItem.objects.values()), snapshot)
                self.assertEqual(list(Club.objects.values()), club_snapshot)
        self.items, self.clubs = original, original_clubs
        self.save()
        self.command('seed_demo')
        self.command('verify_demo')

    def test_corrupt_bytes_empty_text_and_escaping_symlink_fail_atomically(self):
        self.command('seed_demo')
        audio = self.items[2]
        name = audio['audio_file']
        original_audio = (self.static / name).read_bytes()
        for body in (b'<html>upstream error</html>', b'not an audio file', b'RIFF' + b'0' * 100):
            self.write_asset(name, body)
            audio['assets'][1] = self.asset(name)
            self.save()
            with self.assertRaises(CommandError):
                self.command('seed_demo')
        self.write_asset(name, original_audio)
        audio['assets'][1] = self.asset(name)
        text_name = self.items[0]['text_file']
        original_text = (self.data / text_name).read_bytes()
        self.write_asset(text_name, b' \n\n ')
        self.items[0]['assets'][0] = self.asset(text_name)
        self.save()
        with self.assertRaisesMessage(CommandError, 'empty text'):
            self.command('seed_demo')
        self.write_asset(text_name, original_text)
        self.items[0]['assets'][0] = self.asset(text_name)
        (self.root / 'outside.txt').write_text('outside')
        (self.data / 'text/escape.txt').symlink_to(self.root / 'outside.txt')
        self.items[0]['text_file'] = 'text/escape.txt'
        self.save()
        with self.assertRaisesMessage(CommandError, 'escapes allowed root'):
            self.command('seed_demo')
        self.items[0]['text_file'] = text_name
        self.save()
        self.command('seed_demo')
        self.command('verify_demo')

    def test_schema_and_fresh_failure_leave_no_rows(self):
        (self.data / 'media.json').write_text('{"schema_version":2,"items":[]}')
        with self.assertRaisesMessage(CommandError, 'unsupported schema'):
            self.command('seed_demo')
        self.assertEqual(MediaItem.objects.count(), 0)
        self.assertEqual(Club.objects.count(), 0)
        self.save()
        self.command('seed_demo')
        self.command('verify_demo')

    def test_verify_rejects_missing_or_modified_database_and_static_paths(self):
        with self.assertRaisesMessage(CommandError, 'missing database row'):
            self.command('verify_demo')
        self.command('seed_demo')
        for change, expected in [
            (lambda: MediaItem.objects.filter(slug='book-es-01').update(text='Changed'), 'differs from manifest'),
            (lambda: Club.objects.filter(slug='demo-audio-club').update(featured_media=None), 'club missing'),
        ]:
            change()
            with self.assertRaisesMessage(CommandError, expected):
                self.command('verify_demo')
            self.command('seed_demo')
        with patch('catalog.management.commands.verify_demo.finders.find', return_value=None):
            with self.assertRaisesMessage(CommandError, 'no playable static'):
                self.command('verify_demo')

    def test_verify_uses_collected_hashed_storage_and_rejects_missing_hash(self):
        self.command('seed_demo')
        with override_settings(STORAGES={
            'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
            'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'},
        }):
            call_command('collectstatic', interactive=False, verbosity=0)
            self.command('verify_demo')
            from django.contrib.staticfiles.storage import staticfiles_storage
            stored = staticfiles_storage.stored_name(self.items[2]['audio_file'])
            staticfiles_storage.delete(stored)
            with self.assertRaisesMessage(CommandError, 'collected playable asset missing'):
                self.command('verify_demo')

    def test_mp3_and_ogg_signatures_and_mime_validation(self):
        library.validate_audio(b'\xff\xfb\x90\x00' + b'\x01' * 100, 'audio/mpeg', 'fixture.mp3')
        library.validate_audio(b'OggS' + b'\x00' * 20 + b'\x01vorbis', 'audio/ogg', 'fixture.ogg')
        for body, mime in [(b'ID3' + b'\0' * 100, 'audio/mpeg'), (b'OggS' + b'\0' * 100, 'audio/ogg'),
                           (b'<html>error</html>', 'audio/mpeg'), (b'\xff\xfb\x90\x00', 'audio/invalid')]:
            with self.assertRaises(library.LibraryError):
                library.validate_audio(body, mime, 'bad audio')

    def test_audio_directory_symlink_cannot_escape_static_root(self):
        import shutil
        directory = self.static / 'catalog/audio/library'
        outside = self.root / 'external-audio'
        shutil.move(directory, outside)
        directory.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesMessage(CommandError, 'escapes allowed root'):
            self.command('seed_demo')
        self.assertEqual(MediaItem.objects.count(), 0)

    def test_audio_and_text_checksum_corruption_are_rejected(self):
        for item, key in [(self.items[0], 'text_file'), (self.items[2], 'audio_file')]:
            with self.subTest(key=key):
                name = item[key]
                root = self.static if key == 'audio_file' else self.data
                path = root / name
                original = path.read_bytes()
                path.write_bytes(original + b'corrupted')
                with self.assertRaisesMessage(CommandError, 'checksum mismatch'):
                    self.command('seed_demo')
                self.assertEqual(MediaItem.objects.count(), 0)
                path.write_bytes(original)
        self.command('seed_demo')
        self.command('verify_demo')

    def test_schema_clubs_and_missing_files_fail_without_partial_writes(self):
        (self.data / 'clubs.json').write_text('{"schema_version":2,"clubs":[]}')
        with self.assertRaisesMessage(CommandError, 'unsupported schema'):
            self.command('seed_demo')
        self.assertEqual(MediaItem.objects.count(), 0)
        self.save()
        path = self.static / self.items[2]['audio_file']
        body = path.read_bytes()
        path.unlink()
        with self.assertRaisesMessage(CommandError, 'Missing asset'):
            self.command('seed_demo')
        self.assertEqual(MediaItem.objects.count(), 0)
        path.write_bytes(body)
        self.command('seed_demo')
        self.command('verify_demo')

    def test_missing_manifests_fail_loudly_for_both_commands(self):
        for name in ('media.json', 'clubs.json'):
            with self.subTest(name=name):
                path = self.data / name
                original = path.read_bytes()
                path.unlink()
                for command in ('seed_demo', 'verify_demo'):
                    with self.assertRaisesMessage(CommandError, name + ': cannot read JSON manifest'):
                        self.command(command)
                self.assertEqual(MediaItem.objects.count(), 0)
                self.assertEqual(Club.objects.count(), 0)
                path.write_bytes(original)

    def test_manifest_can_include_original_morning_pages_without_duplicate_club(self):
        self.clubs.insert(0, dict(slug='the-morning-pages', name='The Morning Pages', language='Spanish',
                                 description='Welcome! Share a memory from the bakery story.',
                                 featured_media_slug='la-panaderia'))
        self.save()
        self.command('seed_demo')
        original_pk = Club.objects.get(slug='the-morning-pages').pk
        self.command('seed_demo')
        self.assertEqual(Club.objects.count(), 4)
        club = Club.objects.get(slug='the-morning-pages')
        self.assertEqual(club.pk, original_pk)
        self.assertEqual(club.description, self.clubs[0]['description'])
        self.assertIn('4 demo clubs', self.command('verify_demo'))
        self.clubs[0]['featured_media_slug'] = 'missing-story'
        self.save()
        with self.assertRaisesMessage(CommandError, 'invalid featured media'):
            self.command('seed_demo')
