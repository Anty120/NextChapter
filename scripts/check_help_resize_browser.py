"""Real mouse, touch and keyboard resizing without provider or microphone calls."""
import os
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import Client, override_settings

from catalog.models import MediaItem


@override_settings(GEMINI_ENABLED=True, GEMINI_VOICE_INPUT_ENABLED=True, GEMINI_VOICE_INPUT_APPROVED=True)
class HelpResizeBrowserCheck(StaticLiveServerTestCase):
    def test_resize_expand_restore_and_touch(self):
        from playwright.sync_api import expect, sync_playwright
        owner=get_user_model().objects.create_user('help-resize')
        client=Client();client.force_login(owner)
        item=MediaItem.objects.create(slug='help-resize',title='Resize rehearsal',language='French',
            text='Pour moi, un livre est une porte.\n\nBonjour le monde.',published=True)
        artifacts=Path(os.environ.get('NEXTCHAPTER_QA_DIR',str(settings.BASE_DIR/'.venv/qa')))
        artifacts.mkdir(parents=True,exist_ok=True)
        with sync_playwright() as pw:
            options={'headless':True}
            if os.environ.get('ASSISTANCE_BROWSER'):options['executable_path']=os.environ['ASSISTANCE_BROWSER']
            browser=pw.chromium.launch(**options)
            try:
                context=browser.new_context(viewport={'width':1280,'height':1000},reduced_motion='reduce')
                context.add_cookies([{'name':settings.SESSION_COOKIE_NAME,'value':client.cookies[settings.SESSION_COOKIE_NAME].value,'url':self.live_server_url}])
                page=context.new_page();errors=[];calls=[]
                page.on('pageerror',lambda e:errors.append(str(e)))
                page.on('request',lambda r:calls.append(r.url) if '/assist/' in r.url else None)
                page.goto(self.live_server_url+'/media/'+str(item.pk)+'/')
                page.get_by_role('button',name='Speak sentence',exact=False).click()
                panel=page.locator('#assist-panel');body=page.locator('.assist-content');grip=page.get_by_role('button',name='Resize word help',exact=True)
                expect(page.locator('#practice-panel')).to_be_visible()
                compact=panel.bounding_box()
                page.get_by_role('button',name='Expand word help',exact=True).click()
                self.assertAlmostEqual(panel.bounding_box()['width'],760,delta=1)
                self.assertAlmostEqual(panel.bounding_box()['height'],976,delta=1)
                self.assertTrue(page.locator('#assist-close').is_visible())
                self.assertLessEqual(body.evaluate('e=>e.scrollHeight-e.clientHeight'),1)
                page.screenshot(path=str(artifacts/'word-help-expanded.png'))
                page.get_by_role('button',name='Restore word help size',exact=True).click()
                self.assertAlmostEqual(panel.bounding_box()['width'],compact['width'],delta=1)
                grip.focus()
                for _ in range(6):page.keyboard.press('ArrowRight')
                for _ in range(8):page.keyboard.press('ArrowDown')
                custom=panel.bounding_box()
                self.assertGreater(custom['width'],compact['width']+100)
                self.assertGreater(custom['height'],compact['height']+100)
                page.get_by_role('button',name='Expand word help',exact=True).click()
                page.get_by_role('button',name='Restore word help size',exact=True).click()
                self.assertAlmostEqual(panel.bounding_box()['height'],custom['height'],delta=1)
                box=grip.bounding_box();page.mouse.move(box['x']+box['width']/2,box['y']+box['height']/2)
                page.mouse.down();page.mouse.move(box['x']+box['width']/2+140,box['y']+box['height']/2+100,steps=8);page.mouse.up()
                grown=panel.bounding_box();self.assertGreater(grown['width'],custom['width']+100)
                box=grip.bounding_box();page.mouse.move(box['x']+box['width']/2,box['y']+box['height']/2)
                page.mouse.down();page.mouse.move(box['x']+box['width']/2-150,box['y']+box['height']/2-350,steps=8);page.mouse.up()
                shrunk=panel.bounding_box();self.assertLess(shrunk['height'],grown['height']-200)
                self.assertGreater(body.evaluate('e=>e.scrollHeight-e.clientHeight'),0)
                body.evaluate('e=>e.scrollTop=e.scrollHeight')
                self.assertTrue(page.locator('#assist-expand').is_visible());self.assertTrue(grip.is_visible())
                page.locator('#practice-cancel').click();page.keyboard.press('Escape');page.locator('#assist-open').click()
                self.assertAlmostEqual(panel.bounding_box()['width'],shrunk['width'],delta=1)
                for width in [320,390,1280]:
                    page.set_viewport_size({'width':width,'height':844})
                    box=panel.bounding_box();self.assertGreaterEqual(box['x'],11);self.assertLessEqual(box['x']+box['width'],width-11)
                    self.assertGreaterEqual(box['y'],11);self.assertLessEqual(box['y']+box['height'],833)
                    page.locator('#assist-expand').click();box=panel.bounding_box()
                    self.assertLessEqual(box['width'],width-24);self.assertLessEqual(box['height'],820)
                    page.locator('#assist-expand').click()
                touch=browser.new_context(viewport={'width':390,'height':844},has_touch=True,is_mobile=True)
                touch.add_cookies(context.cookies())
                mobile=touch.new_page();mobile.goto(self.live_server_url+'/media/'+str(item.pk)+'/')
                mobile.get_by_role('button',name='Speak sentence',exact=False).tap()
                handle=mobile.locator('#assist-resize').bounding_box();before=mobile.locator('#assist-panel').bounding_box()
                x=handle['x']+handle['width']/2;y=handle['y']+handle['height']/2
                cdp=touch.new_cdp_session(mobile)
                cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
                cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x-45,'y':y-70}]})
                cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
                self.assertLess(mobile.locator('#assist-panel').bounding_box()['height'],before['height']-40)
                self.assertFalse(calls,calls);self.assertFalse(errors,errors)
                print('Resize passed: mouse grow/shrink, keyboard, touch, expand/restore, retained size, internal scroll, viewport clamping and no provider calls.')
            finally:browser.close()
