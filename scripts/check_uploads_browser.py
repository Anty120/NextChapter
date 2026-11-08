"""Real PDF/MP3 upload, private playback, staff review, publication and withdrawal."""
import os
from pathlib import Path
from io import StringIO

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.management import call_command
from django.test import Client

from tests.test_uploads import pdf_bytes, mp3_bytes


class UploadBrowserCheck(StaticLiveServerTestCase):
    def test_upload_read_play_review_and_withdraw(self):
        from playwright.sync_api import expect, sync_playwright

        call_command('seed_demo',stdout=StringIO())
        owner=get_user_model().objects.create_user('upload-browser')
        reviewer=get_user_model().objects.create_superuser('upload-reviewer',password='temporary-test-password')
        sessions=[]
        for user in [owner,reviewer]:
            client=Client();client.force_login(user);sessions.append(client.cookies[settings.SESSION_COOKIE_NAME].value)
        pdf,mp3=pdf_bytes(),mp3_bytes()
        artifacts=Path(os.environ.get('NEXTCHAPTER_QA_DIR',str(settings.BASE_DIR/'.venv/qa')));artifacts.mkdir(parents=True,exist_ok=True)
        with sync_playwright() as pw:
            options={'headless':True}
            if os.environ.get('ASSISTANCE_BROWSER'):options['executable_path']=os.environ['ASSISTANCE_BROWSER']
            browser=pw.chromium.launch(**options)
            try:
                contexts=[]
                for token in sessions:
                    ctx=browser.new_context(viewport={'width':390,'height':844})
                    ctx.add_cookies([{'name':settings.SESSION_COOKIE_NAME,'value':token,'url':self.live_server_url}]);contexts.append(ctx)
                anonymous=browser.new_context(viewport={'width':390,'height':844})
                page=contexts[0].new_page();errors=[];ai=[]
                page.on('pageerror',lambda e:errors.append(str(e)))
                page.on('request',lambda r:ai.append(r.url) if '/assist/' in r.url else None)
                page.goto(self.live_server_url+'/my-library/')
                page.get_by_role('link',name='Upload your first file',exact=True).click()
                page.locator('[type=file]').set_input_files({'name':'My book.pdf','mimeType':'application/pdf','buffer':pdf})
                page.get_by_label('Title:',exact=True).fill('Uploaded test book')
                page.get_by_label('Author or artist (optional):',exact=True).fill('NextChapter test author')
                page.locator('select[name=language]').select_option('French')
                page.get_by_role('checkbox').check()
                page.get_by_role('button',name='Upload to My Library',exact=True).click()
                expect(page.get_by_role('heading',name='Read your PDF',exact=True)).to_be_visible()
                private_url=page.url;identifier=private_url.rstrip('/').split('/')[-1]
                frame=page.locator('iframe.upload-pdf');expect(frame).to_be_visible()
                file_url=frame.get_attribute('src').split('#')[0]
                assert contexts[0].request.get(self.live_server_url+file_url).body().startswith(b'%PDF-')
                self.assertEqual(anonymous.request.get(self.live_server_url+file_url,max_redirects=0).status,302)
                page.wait_for_timeout(1500)
                print('PDF frame inspection:',[(f.url, f.locator('embed').count()) for f in page.frames if '/file/' in f.url])
                page.screenshot(path=str(artifacts/'uploads-pdf-mobile.png'))
                page.get_by_label('Save my page',exact=True).fill('2')
                page.get_by_role('button',name='Save page',exact=True).click()
                expect(page.locator('iframe.upload-pdf')).to_have_attribute('src',file_url+'#page=2')
                page.get_by_role('link',name='Submit for public review',exact=True).click()
                page.locator('select[name=license_name]').select_option('Original work')
                page.locator('textarea[name=rights_note]').fill('Original synthetic test document authored for this browser rehearsal.')
                page.get_by_role('checkbox').check()
                page.get_by_role('button',name='Send to staff for review',exact=True).click()
                expect(page.get_by_role('heading',name='Awaiting review',exact=True)).to_be_visible()
                public=f'{self.live_server_url}/my-library/public/{identifier}/'
                self.assertEqual(anonymous.request.get(public).status,404)
                staff=contexts[1].new_page()
                staff.goto(f'{self.live_server_url}/admin/catalog/uploadedmedia/{identifier}/change/')
                staff.get_by_role('link',name='Open submitted file',exact=True).click()
                expect(staff.get_by_role('heading',name='Read your PDF',exact=True)).to_be_visible()
                staff.get_by_role('link',name='← Staff review',exact=True).click()
                staff.locator('select[name=review_status]').select_option('approved')
                staff.locator('textarea[name=review_notes]').fill('Original synthetic test document approved.')
                staff.locator('input[name=_save]').click()
                self.assertEqual(anonymous.request.get(public).status,200)
                guest=anonymous.new_page();guest.goto(self.live_server_url+'/')
                expect(guest.locator('.community-shelf .book-card')).to_have_count(1)
                guest.locator('.community-shelf .book-card').click()
                expect(guest.get_by_role('heading',name='Read your PDF',exact=True)).to_be_visible()
                page.goto(private_url);page.get_by_role('button',name='Withdraw to private',exact=True).click()
                self.assertEqual(anonymous.request.get(public).status,404)
                page.goto(self.live_server_url+'/my-library/new/')
                page.locator('[type=file]').set_input_files({'name':'My song.mp3','mimeType':'audio/mpeg','buffer':mp3})
                page.get_by_label('Title:',exact=True).fill('Uploaded Spanish audio test')
                page.locator('select[name=language]').select_option('Spanish')
                page.get_by_role('checkbox').check();page.get_by_role('button',name='Upload to My Library',exact=True).click()
                expect(page.locator('#player')).to_be_visible()
                song_url=page.url
                page.locator('#player').evaluate('(a)=>a.play()')
                page.wait_for_function('document.querySelector("#player").currentTime>.2')
                page.locator('#player').evaluate('(a)=>a.pause()')
                with page.expect_response(lambda r:r.url.endswith('/progress/') and r.status==200):
                    page.locator('#player').evaluate('(a)=>{a.currentTime=2.4;}')
                page.reload();page.wait_for_function('document.querySelector("#player").currentTime>2.2')
                self.assertTrue(page.locator('#player').evaluate('(a)=>a.paused'))
                for width in [320,390,1024]:
                    page.set_viewport_size({'width':width,'height':844})
                    for path in ['/my-library/','/my-library/new/',song_url.replace(self.live_server_url,'')]:
                        page.goto(self.live_server_url+path)
                        self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width,path)
                page.goto(self.live_server_url+'/my-library/');page.screenshot(path=str(artifacts/'uploads-library-desktop.png'))
                page.goto(song_url);page.get_by_role('link',name='Delete upload',exact=True).click()
                page.get_by_role('button',name='Delete permanently',exact=True).click()
                self.assertEqual(contexts[0].request.get(song_url).status,404)
                self.assertFalse(errors,errors);self.assertFalse(ai,ai)
                print({'uploads':'passed','pdf_pages':'saved','mp3':'played and resumed','review':'published and withdrawn',
                       'widths':[320,390,1024],'automatic_ai_requests':0})
            finally:browser.close()
