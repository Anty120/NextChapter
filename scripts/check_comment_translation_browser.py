"""Optional Edge/Chromium rehearsal; fixture comments and mocked Gemini only."""
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import Client, override_settings

from catalog.models import Club, Comment


@override_settings(GEMINI_ENABLED=True)
class CommentTranslationBrowserCheck(StaticLiveServerTestCase):
    def test_translation_controls_spoilers_and_errors(self):
        from playwright.sync_api import expect, sync_playwright

        user = get_user_model().objects.create_user('translation-browser')
        club = Club.objects.create(slug='translation-browser', name='Translation circle', language='Spanish')
        normal = Comment.objects.create(user=user, club=club, body='Me gusta este libro.')
        spoiler = Comment.objects.create(user=user, club=club, body='El final es una sorpresa.', spoiler=True)
        session = Client(); session.force_login(user)
        seen, errors = [], []

        def fixture(route):
            self.assertTrue(route.request.headers.get('x-csrftoken'))
            target = route.request.post_data_json['target_language']; seen.append(target)
            if target == 'de':
                route.fulfill(status=429, json={'error':{'message':'Please wait and retry.'}})
            else:
                route.fulfill(json={'translation':f'<b>Translated {target}</b>'})

        with sync_playwright() as pw:
            options = {'headless':True}
            if os.environ.get('ASSISTANCE_BROWSER'):
                options['executable_path'] = os.environ['ASSISTANCE_BROWSER']
            browser = pw.chromium.launch(**options)
            try:
                context = browser.new_context(viewport={'width':320,'height':800})
                context.add_cookies([{'name':settings.SESSION_COOKIE_NAME,
                    'value':session.cookies[settings.SESSION_COOKIE_NAME].value,'url':self.live_server_url}])
                context.route('**/assist/comments/*/translate/', fixture)
                page = context.new_page(); page.on('pageerror', lambda error:errors.append(str(error)))
                page.goto(self.live_server_url+club.get_absolute_url())
                form = page.locator(f'form[data-translation-url="/assist/comments/{normal.pk}/translate/"]')
                hidden = page.locator(f'form[data-translation-url="/assist/comments/{spoiler.pk}/translate/"]')
                expect(hidden).to_be_hidden()
                self.assertFalse(seen, 'Page loading must not send comments to the provider')
                form.get_by_role('button', name='Translate',exact=True).focus()
                page.keyboard.press('Enter')
                expect(form.locator('.translation-text')).to_have_text('<b>Translated en</b>')
                self.assertEqual(form.locator('.translation-text b').count(),0)
                expect(page.get_by_text(normal.body,exact=True)).to_be_visible()
                form.get_by_role('button',name='Hide translation',exact=True).click()
                expect(form.locator('.translation-result')).to_be_hidden()
                form.get_by_role('button',name='Show translation',exact=True).click()
                self.assertEqual(seen,['en'])
                form.get_by_role('combobox').select_option('fr')
                expect(form.locator('.translation-result')).to_be_hidden()
                form.get_by_role('button',name='Translate',exact=True).click()
                expect(form.locator('.translation-text')).to_have_text('<b>Translated fr</b>')
                form.get_by_role('combobox').select_option('de')
                form.get_by_role('button',name='Translate',exact=True).click()
                expect(form.locator('.translation-status')).to_have_text('Please wait and retry.')
                expect(form.get_by_role('button',name='Retry translation',exact=True)).to_be_enabled()
                page.get_by_text('Contains spoilers · show comment',exact=True).click()
                expect(hidden).to_be_visible()
                hidden.get_by_role('button',name='Translate',exact=True).click()
                expect(hidden.locator('.translation-result')).to_be_visible()
                page.get_by_text('Contains spoilers · show comment',exact=True).click()
                expect(hidden.locator('.translation-result')).to_be_hidden()
                self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),320)
                page.set_viewport_size({'width':1024,'height':800})
                self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),1024)
                self.assertFalse(errors,errors)
            finally:
                browser.close()
