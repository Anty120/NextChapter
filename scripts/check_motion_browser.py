"""Optional real-browser check of local Motion, accessibility and fallbacks."""
from io import StringIO
import os
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.management import call_command
from django.test import Client, override_settings

from catalog.models import Club, Comment, MediaItem


@override_settings(GEMINI_ENABLED=True)
class MotionBrowserCheck(StaticLiveServerTestCase):
    def test_motion_and_progressive_fallbacks(self):
        from playwright.sync_api import expect, sync_playwright

        call_command('seed_demo', stdout=StringIO())
        user = get_user_model().objects.create_user('motion-rehearsal')
        club = Club.objects.first()
        Comment.objects.create(club=club, user=user, body='A synthetic test comment.')
        story = MediaItem.objects.get(slug='le-livre-jaune')
        book = MediaItem.objects.get(slug='book-es-01')
        session = Client(); session.force_login(user)
        receipts, errors, remote_requests = [], [], []
        artifacts = Path(os.environ.get('NEXTCHAPTER_QA_DIR', str(settings.BASE_DIR / '.venv' / 'qa')))
        artifacts.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as pw:
            options = {'headless':True}
            if os.environ.get('ASSISTANCE_BROWSER'):
                options['executable_path'] = os.environ['ASSISTANCE_BROWSER']
            browser = pw.chromium.launch(**options)
            try:
                context = browser.new_context(viewport={'width':1440,'height':1000})
                page = context.new_page(); page.on('pageerror', lambda e:errors.append(str(e)))
                page.on('request', lambda r:remote_requests.append(r.url) if not r.url.startswith(self.live_server_url) else None)
                page.goto(self.live_server_url + '/')
                expect(page.locator('html')).to_have_attribute('data-ui-motion','enabled')
                self.assertTrue(page.evaluate('typeof Motion.animate === "function"'))
                card = page.locator('.book-card').first
                expect(card).to_be_visible()
                page.wait_for_function('document.querySelector(".book-card").getAnimations().length === 0')
                card.hover()
                page.wait_for_function('new DOMMatrixReadOnly(getComputedStyle(document.querySelector(".book-card")).transform).m42 < -3')
                page.mouse.down()
                page.wait_for_function('new DOMMatrixReadOnly(getComputedStyle(document.querySelector(".book-card")).transform).m11 < .99')
                page.mouse.move(5,5); page.mouse.up()
                page.wait_for_function('Math.abs(new DOMMatrixReadOnly(getComputedStyle(document.querySelector(".book-card")).transform).m42) < .1')
                page.wait_for_function('document.querySelector(".book-card").getAnimations().length === 0')
                page.evaluate('scrollTo({top:0,behavior:"instant"})')
                page.screenshot(path=str(artifacts / 'motion-after-desktop.png'))
                for width in [320,390]:
                    page.set_viewport_size({'width':width,'height':844})
                    for path in ['/', '/?format=audio', '/clubs/', club.get_absolute_url(), story.get_absolute_url(),
                                 f'/media/{book.pk}/quiz/', '/accounts/login/']:
                        page.goto(self.live_server_url + path)
                        self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), width, path)
                        expect(page.get_by_role('link',name='Skip to content')).to_be_attached()
                        page.locator('body').evaluate('(e)=>{e.tabIndex=-1;e.focus();e.removeAttribute("tabindex");}')
                        page.keyboard.press('Tab'); expect(page.get_by_role('link',name='Skip to content')).to_be_focused()
                        page.keyboard.press('Enter'); expect(page.locator('main')).to_be_focused()
                    page.goto(self.live_server_url + '/')
                    page.wait_for_function('document.querySelectorAll(".book-card")[0].getAnimations().length === 0')
                    page.evaluate('scrollTo({top:0,behavior:"instant"})')
                    page.screenshot(path=str(artifacts / f'motion-after-{width}.png'))
                page.emulate_media(reduced_motion='reduce')
                expect(page.locator('html')).to_have_attribute('data-ui-motion','reduced')
                card.hover()
                self.assertEqual(page.evaluate('document.querySelector(".book-card").getAnimations().length'),0)
                self.assertEqual(page.locator('.book-card').first.evaluate('(e)=>getComputedStyle(e).transform'),'none')
                page.emulate_media(reduced_motion='no-preference')
                expect(page.locator('html')).to_have_attribute('data-ui-motion','enabled')
                # A linked reading position is preserved; no entrance animation moves it.
                context.add_cookies([{'name':settings.SESSION_COOKIE_NAME,
                    'value':session.cookies[settings.SESSION_COOKIE_NAME].value,'url':self.live_server_url}])
                page.goto(self.live_server_url + book.get_absolute_url() + '#paragraph-20')
                expect(page.locator('#paragraph-20')).to_be_in_viewport()
                self.assertGreater(page.evaluate('scrollY'),0)
                self.assertEqual(page.locator('.paragraph').evaluate_all('(nodes)=>nodes.reduce((n,e)=>n+e.getAnimations().length,0)'),0)
                # Popup animation changes opacity only, retaining its anchored position.
                page.goto(self.live_server_url + story.get_absolute_url())
                page.get_by_role('button',name='Word help',exact=True).click()
                expect(page.locator('#assist-panel')).to_be_visible()
                self.assertEqual(page.locator('#assist-panel').evaluate('(e)=>getComputedStyle(e).transform'),'none')
                page.keyboard.press('Escape'); expect(page.locator('#assist-panel')).to_be_hidden()
                context.close()
                for mode in ['missing-vendor','no-javascript']:
                    fallback = browser.new_context(viewport={'width':390,'height':844},java_script_enabled=mode!='no-javascript')
                    if mode=='missing-vendor':
                        fallback.route('**/vendor/motion/**',lambda route:route.abort())
                    tab = fallback.new_page();tab.on('pageerror',lambda e:errors.append(str(e)))
                    tab.goto(self.live_server_url + '/')
                    expect(tab.locator('.book-card').first).to_be_visible()
                    tab.locator('select[name=format]').select_option('audio')
                    tab.get_by_role('button',name='Find a story',exact=False).click()
                    expect(tab).to_have_url(self.live_server_url+'/?q=&language=&format=audio&level=')
                    self.assertEqual(tab.locator('.book-card').count(),4)
                    fallback.close();receipts.append(mode)
                self.assertFalse(errors,errors)
                self.assertFalse(remote_requests,remote_requests)
                print({'motion':'passed','widths':[320,390,1440], 'reduced_motion':'passed',
                       'fallbacks':receipts,'hash_position':'passed','remote_runtime_requests':0})
            finally:
                browser.close()
