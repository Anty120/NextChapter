"""Exercise a real 10 MB upload and bounded playback/download in a browser."""
import hashlib
import os
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import Client

from tests.test_large_songs import large_mp3


class LargeSongBrowserCheck(StaticLiveServerTestCase):
    def test_full_size_song(self):
        from playwright.sync_api import expect, sync_playwright
        owner=get_user_model().objects.create_user('large-song-browser')
        client=Client();client.force_login(owner)
        token=client.cookies[settings.SESSION_COOKIE_NAME].value
        raw=large_mp3()
        with sync_playwright() as pw:
            options={'headless':True}
            if os.environ.get('ASSISTANCE_BROWSER'):options['executable_path']=os.environ['ASSISTANCE_BROWSER']
            browser=pw.chromium.launch(**options)
            try:
                context=browser.new_context(viewport={'width':390,'height':844},accept_downloads=True)
                context.add_cookies([{'name':settings.SESSION_COOKIE_NAME,'value':token,'url':self.live_server_url}])
                page=context.new_page();errors=[];chunks=[]
                page.on('pageerror',lambda e:errors.append(str(e)))
                page.on('request',lambda r:chunks.append(int(r.all_headers().get('content-length','0'))) if '/chunk/' in r.url else None)
                page.goto(self.live_server_url+'/my-library/new/')
                page.locator('[type=file]').set_input_files({'name':'Full size song.mp3','mimeType':'audio/mpeg','buffer':raw})
                self.assertEqual(page.locator('[type=file]').evaluate('(e)=>e.validationMessage'),'')
                page.locator('select[name=language]').select_option('Spanish')
                page.get_by_role('checkbox').check()
                page.get_by_role('button',name='Upload to My Library',exact=True).click()
                expect(page.get_by_role('heading',name='Listen to your song',exact=True)).to_be_visible(timeout=30000)
                self.assertEqual(sum(chunks),10_000_000);self.assertLessEqual(max(chunks),1048576)
                page.locator('#player').evaluate('(a)=>a.play()')
                page.wait_for_function('document.querySelector("#player").currentTime>.2')
                page.locator('#player').evaluate('(a)=>a.pause()')
                with page.expect_response(lambda r:r.url.endswith('/progress/') and r.status==200):
                    page.locator('#player').evaluate('(a)=>{a.currentTime=a.duration*.9;}')
                page.wait_for_function('document.querySelector("#player").readyState>=2')
                page.locator('#player').evaluate('(a)=>a.play()')
                page.wait_for_function('!document.querySelector("#player").paused && !document.querySelector("#player").seeking')
                page.locator('#player').evaluate('(a)=>a.pause()')
                page.reload();page.wait_for_function('document.querySelector("#player").currentTime>10')
                self.assertTrue(page.locator('#player').evaluate('(a)=>a.paused'))
                page.get_by_role('link',name='Download MP3',exact=True).click()
                expect(page.get_by_role('button',name='Download MP3',exact=True)).to_be_visible()
                with page.expect_download() as info:page.get_by_role('button',name='Download MP3',exact=True).click()
                download=info.value
                self.assertEqual(hashlib.sha256(Path(download.path()).read_bytes()).hexdigest(),hashlib.sha256(raw).hexdigest())
                download.delete()
                for width in [320,390]:
                    page.set_viewport_size({'width':width,'height':844})
                    self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width)
                page.goto(self.live_server_url+'/my-library/new/')
                page.locator('[type=file]').set_input_files({'name':'Too large.mp3','mimeType':'audio/mpeg','buffer':raw+b'x'})
                self.assertIn('10 MB',page.locator('[type=file]').evaluate('(e)=>e.validationMessage'))
                self.assertFalse(errors,errors)
                print({'bytes':len(raw),'max_request_bytes':max(chunks),'audio':'played, sought, resumed','download':'SHA-256 matched','mobile_widths':[320,390]})
            finally:browser.close()
