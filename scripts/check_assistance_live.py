"""Opt-in live provider/browser smoke; quota is consumed, no personal audio used.

Run via manage.py test scripts.check_assistance_live with NC_LIVE_GEMINI=1,
backend Gemini configuration, Playwright and Chromium/ASSISTANCE_BROWSER.
Use local SQLite, never a shared DATABASE_URL. Human sound-quality acceptance is
separate: the microphone source here is generated public reference speech.
"""
import json
import os
from pathlib import Path
import tempfile
from unittest import skipUnless

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import Client, override_settings

from assistance import provider
from catalog.models import MediaItem


@skipUnless(os.environ.get('NC_LIVE_GEMINI') == '1', 'Explicit live-provider opt-in required.')
@override_settings(APP_ENV='test', GEMINI_CACHE_TTL_SECONDS=0,
                   CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
class LiveAssistanceCheck(StaticLiveServerTestCase):
    def test_real_provider_with_synthetic_microphone(self):
        from playwright.sync_api import expect, sync_playwright

        self.assertTrue(settings.GEMINI_ENABLED)
        self.assertTrue(settings.GEMINI_VOICE_INPUT_ENABLED and settings.GEMINI_VOICE_INPUT_APPROVED)
        user = get_user_model().objects.create_user('live-synthetic-check')
        text = 'Pour moi, un livre est une porte.'
        item = MediaItem.objects.create(slug='live-reference', title='Live public reference',
            language='French', text=text, published=True)
        client = Client()
        client.force_login(user)
        reference = {'selection': text, 'context': text, 'language': 'fr-FR', 'explanation_locale': 'en'}
        with tempfile.TemporaryDirectory(prefix='nextchapter-public-reference-') as directory:
            microphone = Path(directory) / 'public-reference.wav'
            microphone.write_bytes(provider.pronounce(reference))
            with sync_playwright() as pw:
                options = {'headless': True, 'args': ['--use-fake-device-for-media-stream',
                    '--use-fake-ui-for-media-stream', f'--use-file-for-fake-audio-capture={microphone}']}
                if os.environ.get('ASSISTANCE_BROWSER'):
                    options['executable_path'] = os.environ['ASSISTANCE_BROWSER']
                browser = pw.chromium.launch(**options)
                try:
                    context = browser.new_context(viewport={'width': 390, 'height': 844})
                    context.add_cookies([{'name': settings.SESSION_COOKIE_NAME,
                        'value': client.cookies[settings.SESSION_COOKIE_NAME].value, 'url': self.live_server_url}])
                    page = context.new_page()
                    responses = []
                    page.on('response', lambda r: responses.append({'path': r.url.split('/assist/')[-1],
                        'status': r.status}) if '/assist/' in r.url else None)
                    page.goto(f'{self.live_server_url}/media/{item.pk}/')
                    page.locator('#assist-open').click()
                    page.locator('#assist-passage').select_option('5:8')
                    page.locator('#assist-explain').click()
                    expect(page.locator('#assist-result')).to_be_visible(timeout=45000)
                    expect(page.locator('#assist-definitions')).to_contain_text('mwa')
                    page.locator('#assist-listen').click()
                    expect(page.locator('#assist-status')).to_contain_text('Playing', timeout=45000)
                    page.locator('#assist-practice').click()
                    page.locator('#practice-record').click()
                    expect(page.locator('#practice-status')).to_contain_text('Recording locally')
                    expect(page.locator('#practice-target')).to_have_text(text)
                    page.wait_for_timeout(4500)
                    page.locator('#practice-stop').click()
                    page.locator('#practice-replay').evaluate('(audio) => audio.play()')
                    page.locator('#practice-analyze').click()
                    expect(page.locator('#practice-results')).to_be_visible(timeout=45000)
                    self.assertTrue(page.locator('#practice-transcript').inner_text().strip())
                    self.assertEqual(responses, [{'path': path, 'status': 200}
                        for path in ('lookup/', 'pronounce/', 'practice/')])
                    page.locator('#practice-discard').click()
                    expect(page.locator('#practice-results')).to_be_hidden()
                    page.locator('#practice-cancel').click()
                    page.locator('#assist-close').click()
                    page.get_by_role('button', name='Pronunciation hints', exact=True).click()
                    expect(page.locator('.phonetic-word')).to_have_count(7, timeout=45000)
                    print(json.dumps({'live_browser': 'passed', 'responses': responses,
                        'input': 'generated public French reference through browser microphone capture',
                        'assessment_quality': 'not benchmarked'}))
                finally:
                    browser.close()
