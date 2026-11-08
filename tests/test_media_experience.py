"""Reader contract tests; the temporary helper exists only until #12 is integrated."""
import importlib.util
import sys
from types import ModuleType
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from catalog.models import Club, MediaItem, ReadingProgress

# Do not create catalog/library.py in another worker's exclusive scope.
if 'catalog.library' not in sys.modules and importlib.util.find_spec('catalog.library') is None:
    helper = ModuleType('catalog.library')
    helper.get_media_metadata = lambda slug: {}
    sys.modules['catalog.library'] = helper


@override_settings(STORAGES={
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
})
class MediaExperienceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('reader', password='local-test-pass')
        self.other = get_user_model().objects.create_user('other', password='local-test-pass')
        self.metadata = {}
        self.helper = patch('catalog.library.get_media_metadata', side_effect=lambda slug: self.metadata.get(slug, {}))
        self.helper.start()
        self.addCleanup(self.helper.stop)

    def item(self, slug='custom', **kwargs):
        fields = dict(title='Complete work', creator='Author', language='Spanish', format='book',
                      level='C1', description='A complete book', text='First paragraph.\n\nLast paragraph.',
                      attribution='Text credit', cultural_context='Historical context', published=True)
        fields.update(kwargs)
        return MediaItem.objects.create(slug=slug, **fields)

    def test_both_complete_books_have_toc_and_private_bookmarks(self):
        self.client.force_login(self.user)
        for slug in ('book-es-01', 'book-en-01'):
            with self.subTest(slug=slug):
                item = self.item(slug, text='\n\n'.join(f'Full paragraph {i}' for i in range(1200)))
                self.metadata[slug] = {'chapters': [{'title': 'Opening', 'start_paragraph': 0},
                                                      {'title': 'Ending', 'start_paragraph': 1199}]}
                response = self.client.get(item.get_absolute_url())
                self.assertContains(response, 'Full paragraph 1199')
                self.assertContains(response, 'href="#paragraph-1199"')
                self.assertContains(response, 'aria-label="Table of contents"')
                url = reverse('save_progress', args=[item.pk])
                self.assertRedirects(self.client.post(url, {'paragraph': 1199, 'user': self.other.pk}),
                                     item.get_absolute_url() + '#paragraph-1199')
                response = self.client.get(item.get_absolute_url())
                self.assertContains(response, 'Return to your saved paragraph')
                self.assertEqual(response.context['progress'].paragraph, 1199)
                self.assertFalse(ReadingProgress.objects.filter(user=self.other).exists())
                self.client.force_login(self.other)
                self.assertIsNone(self.client.get(item.get_absolute_url()).context['progress'])
                self.client.force_login(self.user)

    def test_audio_formats_credits_transcripts_and_nonzero_resume(self):
        self.client.force_login(self.user)
        for slug, fmt, mime, ext in (
            ('audiobook-es-01', 'audiobook', 'audio/mpeg', 'mp3'),
            ('audiobook-en-01', 'audiobook', 'audio/mpeg', 'mp3'),
            ('song-en-01', 'song', 'audio/ogg', 'ogg'),
            ('song-en-02', 'song', 'audio/ogg', 'ogg'),
        ):
            with self.subTest(slug=slug):
                item = self.item(slug, format=fmt, audio_file=f'catalog/audio/library/{slug}.{ext}')
                self.metadata[slug] = {'audio_mime': mime, 'duration_seconds': 125, 'performer': 'Human singer',
                                       'excerpt': fmt == 'audiobook', 'sources': [
                                           {'component': 'recording', 'creator': 'Archivist',
                                            'source_url': 'https://example.org/recording', 'license': 'Public domain',
                                            'license_url': 'https://example.org/license', 'rights_territory': 'USA'}]}
                self.assertEqual(self.client.post(reverse('save_progress', args=[item.pk]),
                                                 {'seconds': 17.5}, HTTP_ACCEPT='application/json').status_code, 200)
                response = self.client.get(item.get_absolute_url())
                for text in (f'type="{mime}"', 'data-seconds="17.5"', 'Human singer', '2:05', 'Archivist', 'USA', 'First paragraph.'):
                    self.assertContains(response, text)
                self.assertNotContains(response, 'synthetic narration')
                self.assertNotContains(response, 'autoplay=')
                self.assertContains(response, 'Playback speed' if fmt == 'audiobook' else '<h2>Lyrics</h2>')

    def test_custom_items_and_missing_content_are_truthful(self):
        item = self.item(format='song', text='', audio_file='catalog/audio/custom.mp3')
        response = self.client.get(item.get_absolute_url())
        self.assertContains(response, 'type="audio/mpeg"')
        self.assertContains(response, 'Lyrics are not available for reuse')
        item.audio_file = ''
        item.save()
        self.assertContains(self.client.get(item.get_absolute_url()), 'A recording is not available')

    def test_controls_language_and_club_links_use_actual_relationships(self):
        self.client.force_login(self.user)
        item = self.item()
        club = Club.objects.create(slug='custom-circle', name='Custom circle', language='Spanish', featured_media=item)
        response = self.client.get(item.get_absolute_url())
        self.assertContains(response, '<p lang="es">First paragraph.</p>', html=True)
        self.assertNotContains(response, '<article lang=')
        self.assertContains(response, 'aria-label="Save my place at paragraph 1"')
        self.assertContains(response, club.get_absolute_url())

    def test_drafts_anonymous_csrf_and_invalid_positions(self):
        item = self.item()
        url = reverse('save_progress', args=[item.pk])
        self.assertEqual(self.client.post(url, {'paragraph': 1}).status_code, 302)
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(url, {'paragraph': 2}).status_code, 400)
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.user)
        self.assertEqual(strict.post(url, {'paragraph': 1}).status_code, 403)
        item.published = False
        item.save()
        self.assertEqual(self.client.get(item.get_absolute_url()).status_code, 404)
        self.assertEqual(self.client.post(url, {'paragraph': 1}).status_code, 404)


def check_player_browser(page, base_url, audio_url):
    """Optional Playwright check for both metadata orders and the paused-seek race.

    Accepts an existing page and an actual bundled audio URL; no browser dependency
    is added to the ordinary Django suite. Integration can reuse this with new bytes.
    """
    from html import escape

    page.goto(base_url)
    script = base_url + '/static/catalog/player.js'
    for metadata_first in (True, False):
        requests = []
        page.route('**/fixture-progress', lambda route: (
            requests.append(route.request.post_data),
            route.fulfill(status=200, content_type='application/json', body='{"saved":true}')
        ))
        page.set_content(
            '<audio id="player" controls data-seconds="17" '
            f'preload="{"metadata" if metadata_first else "none"}" '
            f'src="{escape(audio_url, quote=True)}"></audio>'
            '<p id="audio-error" hidden></p><form id="audio-progress" '
            f'action="{base_url}/fixture-progress"><input id="audio-seconds" name="seconds" '
            'value="17"><p id="save-status"></p></form>'
            '<select id="playback-speed"><option value="1">1</option><option value="1.5">1.5</option></select>'
        )
        if metadata_first:
            page.wait_for_function('document.querySelector("audio").readyState >= 1')
        page.add_script_tag(url=script)
        if not metadata_first:
            # Before metadata, backgrounding/pausing must not save an initial zero.
            page.evaluate('window.dispatchEvent(new Event("pagehide"))')
            assert not requests, 'Restoration overwrote progress before metadata'
            page.locator('audio').evaluate('(audio) => audio.load()')
        page.wait_for_function('Math.abs(document.querySelector("audio").currentTime - 17) < 0.1 && !document.querySelector("audio").seeking')
        assert page.locator('audio').evaluate('(audio) => audio.paused'), 'Restore autoplayed'
        assert not requests, 'Restoring a saved timestamp should not issue a write'
        page.select_option('#playback-speed', '1.5')
        assert page.locator('audio').evaluate('(audio) => audio.playbackRate') == 1.5
        # A seek while paused must save even though no new pause event fires.
        page.locator('audio').evaluate('(audio) => { audio.pause(); audio.currentTime = 12; }')
        page.wait_for_function('document.querySelector("#save-status").textContent === "Your listening position is saved."')
        assert requests and '12.0' in requests[-1], requests
        page.locator('audio').evaluate('(audio) => audio.play()')
        page.wait_for_function('document.querySelector("audio").currentTime > 12.5')
        page.locator('audio').evaluate('(audio) => audio.pause()')
        page.unroute('**/fixture-progress')
