"""Optional Edge/Chromium check: local non-English playback and book quizzes."""
from io import StringIO
import os

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.management import call_command

from catalog.models import MediaItem


class LearningBrowserCheck(StaticLiveServerTestCase):
    def test_bundled_audio_and_quizzes(self):
        from playwright.sync_api import expect, sync_playwright

        call_command('seed_demo', stdout=StringIO())
        recordings = list(MediaItem.objects.filter(published=True, format__in=['song','audiobook']))
        books = list(MediaItem.objects.filter(published=True, format='book'))
        with sync_playwright() as pw:
            options = {'headless': True}
            if os.environ.get('ASSISTANCE_BROWSER'):
                options['executable_path'] = os.environ['ASSISTANCE_BROWSER']
            browser = pw.chromium.launch(**options)
            try:
                page = browser.new_page(viewport={'width':320, 'height':800})
                for item in recordings:
                    self.assertIn(item.language, ['French','Spanish'])
                    page.goto(self.live_server_url + item.get_absolute_url())
                    player = page.locator('#player')
                    player.evaluate('(a) => a.play()')
                    page.wait_for_function('document.querySelector("#player").currentTime > 0.2')
                    self.assertFalse(player.evaluate('(a) => a.error !== null'))
                    self.assertGreater(player.evaluate('(a) => a.duration'), 20)
                    player.evaluate('(a) => {a.pause(); a.currentTime=10;}')
                    self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), 320)
                for book in books:
                    page.goto(f'{self.live_server_url}/media/{book.pk}/quiz/')
                    expect(page.locator('fieldset')).to_have_count(5)
                    for fieldset in page.locator('fieldset').all():
                        fieldset.get_by_role('radio').first.check()
                    page.get_by_role('button', name='Check my answers').click()
                    expect(page.locator('h2[role=status]')).to_contain_text('of 5 correct')
                    self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), 320)
            finally:
                browser.close()
