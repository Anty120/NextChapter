"""Optional real-browser rehearsal: manage.py test scripts.check_assistance_browser.

Requires Playwright and Chromium (or ASSISTANCE_BROWSER executable). Uses a
temporary Django test database, mocked provider responses and synthetic audio.
No credentials, personal microphone input or external provider calls are used.
"""
import io
import json
import os
import re
from pathlib import Path
import struct
import tempfile
import time
import wave

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, override_settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from catalog.models import MediaItem


@override_settings(GEMINI_ENABLED=True, GEMINI_API_KEY='', GEMINI_TEXT_MODEL='',
                   GEMINI_VOICE_INPUT_ENABLED=True, GEMINI_VOICE_INPUT_APPROVED=True)
class AssistanceBrowserCheck(StaticLiveServerTestCase):
    def test_reader_and_recording(self):
        from playwright.sync_api import expect, sync_playwright

        user = get_user_model().objects.create_user('browser-rehearsal')
        item = MediaItem.objects.create(slug='browser-reference', title='Browser reference',
            creator='NextChapter', format='story', level='A2', description='A short French passage for word help.',
            language='French', text='😀 Pour moi, un livre est une porte.\n\nBonjour le monde.', published=True)
        session = Client()
        session.force_login(user)
        audio = io.BytesIO()
        with wave.open(audio, 'wb') as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(16000)
            output.writeframes(struct.pack('<hh', 1200, -1200) * 8000)
        seen, attempts, errors = [], [], []
        failure = [False]
        expected_offsets = [(7, 10)]

        def provider_fixture(route):
            request = route.request
            self.assertTrue(request.headers.get('x-csrftoken'))
            seen.append(request.url)
            if failure[0]:
                route.fulfill(status=429, json={'error': {'code': 'rate_limited', 'message': 'Wait and retry.'}})
            elif request.url.endswith('/pronounce/'):
                route.fulfill(content_type='audio/wav', body=audio.getvalue())
            elif request.url.endswith('/phonetics/'):
                ref = request.post_data_json
                selection = item.paragraphs[ref['paragraph']][ref['start']:ref['end']]
                words = [{'start':m.start(),'end':m.end(),'text':m.group(),'ipa':'test','sound':'hint'}
                         for m in re.finditer(r"[^\W\d_]+", selection)]
                route.fulfill(json={'words':words,'notice':'Approximate fixture'})
            elif request.url.endswith('/practice/'):
                self.assertIn(b'name="start"\r\n\r\n0', request.post_data_buffer)
                self.assertIn(('name="end"\r\n\r\n' + str(len(item.paragraphs[0]))).encode(), request.post_data_buffer)
                time.sleep(0.3)  # Keep Analyze pending across the double click.
                body = request.post_data_buffer
                index = body.index(b'RIFF')
                end = body.index(b'\r\n--', index)
                with wave.open(io.BytesIO(body[index:end]), 'rb') as attempt:
                    self.assertEqual(attempt.getnchannels(), 1)
                    self.assertEqual(attempt.getsampwidth(), 2)
                    duration = attempt.getnframes() / attempt.getframerate()
                    self.assertGreater(duration, 0)
                    self.assertLessEqual(duration, 60)
                    attempts.append(duration)
                route.fulfill(json={'transcript': 'moi', 'reference_match': 'Similar words; not a score.',
                    'feedback': [], 'assessment_supported': False, 'uncertainty': 'Synthetic UI fixture; no assessment.'})
            else:
                payload = request.post_data_json
                self.assertEqual((payload['start'], payload['end']), expected_offsets[0])
                route.fulfill(json={'language': 'fr-FR', 'meaning': '<b>me</b>', 'translation': 'me',
                    'ipa': '/mwa/', 'sound_guidance': 'French oi is /wa/.', 'approximation': 'roughly wah',
                    'examples': [{'text': 'moi', 'note': 'Approximation varies by accent.'}],
                    'caveat': 'An approximation.', 'uncertainty': 'Fixture only.'})

        with sync_playwright() as pw:
            options = {'headless': True, 'args': ['--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream']}
            executable = os.environ.get('ASSISTANCE_BROWSER')
            if executable:
                options['executable_path'] = executable
            browser = pw.chromium.launch(**options)
            try:
                context = browser.new_context(viewport={'width': 320, 'height': 800})
                context.add_cookies([{'name': settings.SESSION_COOKIE_NAME,
                    'value': session.cookies[settings.SESSION_COOKIE_NAME].value, 'url': self.live_server_url}])
                context.add_init_script("""window.capturedTracks = [];
                    const originalCapture = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
                    navigator.mediaDevices.getUserMedia = async (...args) => {
                      const stream = await originalCapture(...args);
                      stream.getTracks().forEach(track => {
                        const stop = track.stop.bind(track);
                        track.stop = () => { stop(); localStorage.setItem('qa-stopped-tracks',
                          String(Number(localStorage.getItem('qa-stopped-tracks') || 0) + 1)); };
                      });
                      window.capturedTracks.push(...stream.getTracks()); return stream;
                    }; window.captureAllowed = navigator.mediaDevices.getUserMedia;""")
                context.route('**/assist/**', provider_fixture)
                page = context.new_page()
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(f'{self.live_server_url}/media/{item.pk}/')
                context.grant_permissions(['clipboard-read', 'clipboard-write'])
                page.locator('#paragraph-0 p').scroll_into_view_if_needed()
                initial_scroll = page.evaluate('window.scrollY')
                # Real DOM selection crosses an astral character: offsets must be codepoints.
                page.evaluate("""() => { const text = document.querySelector('#paragraph-0 p').firstChild;
                    const r = document.createRange(); r.setStart(text, 8); r.setEnd(text, 11);
                    const s = getSelection(); s.removeAllRanges(); s.addRange(r); }""")
                page.locator('.story-text').dispatch_event('pointerup')
                expect(page.locator('#assist-selection')).to_have_text('moi')
                self.assertEqual(page.evaluate('window.scrollY'), initial_scroll, 'Selection must not jump the reader to a panel')
                popup = page.locator('#assist-panel').bounding_box()
                self.assertLessEqual(popup['width'], 340)
                self.assertLess(popup['height'], 260)
                self.assertGreaterEqual(popup['x'], 10)
                self.assertLessEqual(popup['x'] + popup['width'], 310)
                self.assertFalse(page.locator('#assist-picker').evaluate('(d) => d.open'))
                page.locator('#assist-copy').click()
                self.assertEqual(page.evaluate('navigator.clipboard.readText()'), 'moi')
                page.locator('#assist-explain').click()
                expect(page.locator('#assist-result')).to_be_visible()
                self.assertLess(page.locator('#assist-panel').bounding_box()['height'], 260)
                artifacts = Path(tempfile.gettempdir()) / 'nextchapter-assistance-qa'
                artifacts.mkdir(exist_ok=True)
                page.screenshot(path=str(artifacts / 'popup-320.png'))
                page.set_viewport_size({'width': 390, 'height': 844})
                self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), 390)
                page.set_viewport_size({'width': 1024, 'height': 800})
                page.screenshot(path=str(artifacts / 'popup-desktop.png'))
                page.set_viewport_size({'width': 320, 'height': 800})
                expect(page.locator('#assist-definitions')).to_contain_text('<b>me</b>')
                self.assertEqual(page.locator('#assist-definitions b').count(), 0)
                page.evaluate('getSelection().removeAllRanges()')
                page.locator('#assist-listen').click()
                expect(page.locator('#assist-status')).to_contain_text('Playing')
                page.locator('#assist-details > summary').click()
                page.locator('#assist-speed').select_option('0.75')
                page.locator('#assist-stop').click()
                failure[0] = True
                page.locator('#assist-deeper').click()
                expect(page.locator('#assist-status')).to_have_text('Wait and retry.')
                failure[0] = False
                page.locator('#assist-practice').click()
                self.assertEqual(page.evaluate('capturedTracks.length'), 0)
                page.locator('#practice-reference').click()
                expect(page.locator('#practice-status')).to_contain_text('Playing the reference')
                page.locator('#assist-listen').click()
                expect(page.locator('#assist-status')).to_contain_text('Playing pronunciation')
                self.assertTrue(page.locator('#practice-reference-audio').evaluate('(a) => a.paused'))
                count = len(seen)
                page.locator('#practice-record').click()
                expect(page.locator('#practice-status')).to_contain_text('Recording locally')
                expect(page.locator('#assist-listen')).to_be_disabled()
                page.wait_for_timeout(1200)
                page.locator('#practice-stop').click()
                self.assertEqual(len(seen), count, 'Capture must not upload automatically')
                self.assertTrue(page.evaluate('capturedTracks.every(t => t.readyState === "ended")'))
                expect(page.locator('#practice-analyze')).to_be_enabled()
                page.locator('#practice-replay').evaluate('(audio) => audio.play()')
                page.locator('#practice-analyze').click()
                expect(page.locator('#practice-results')).to_be_visible()
                expect(page.locator('#practice-feedback')).to_contain_text('could not be assessed')
                self.assertEqual(len(attempts), 1)
                page.locator('#practice-discard').click()
                expect(page.locator('#practice-analyze')).to_be_disabled()
                self.assertFalse(page.locator('#practice-replay').get_attribute('src'))
                page.locator('#practice-record').click()
                expect(page.locator('#practice-status')).to_contain_text('Recording locally')
                page.locator('#practice-cancel').click()
                expect(page.locator('#practice-panel')).to_be_hidden()
                self.assertTrue(page.evaluate('capturedTracks.every(t => t.readyState === "ended")'))
                # Automatic hard stop and duplicate Analyze protection.
                page.locator('#assist-practice').click()
                page.locator('#practice-record').click()
                expect(page.locator('#practice-status')).to_contain_text('Recording stopped', timeout=65000)
                self.assertTrue(page.evaluate('capturedTracks.every(t => t.readyState === "ended")'))
                page.locator('#practice-analyze').dblclick()
                expect(page.locator('#practice-results')).to_be_visible()
                self.assertEqual(len(attempts), 2)
                page.locator('#practice-discard').click()
                page.evaluate("""() => { navigator.mediaDevices.getUserMedia = async () => {
                    throw new DOMException('Denied in rehearsal', 'NotAllowedError'); }; }""")
                page.locator('#practice-record').click()
                expect(page.locator('#practice-status')).to_contain_text('permission was denied')
                page.locator('#practice-cancel').click()
                self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), 320)
                # Keyboard-only entry and sentence/word picker.
                page.locator('#assist-close').click()
                page.locator('#assist-open').focus()
                page.keyboard.press('Enter')
                expect(page.locator('#assist-title')).to_be_focused()
                page.evaluate("""() => { const text = document.querySelector('#paragraph-0 p').firstChild;
                    const r = document.createRange(); r.setStart(text, 8); r.setEnd(text, 11);
                    const s = getSelection(); s.removeAllRanges(); s.addRange(r); }""")
                page.locator('#assist-paragraph').select_option('1')
                page.locator('#assist-passage').select_option('0:7')
                expect(page.locator('#assist-selection')).to_have_text('Bonjour')
                expected_offsets[0] = (0, 7)
                page.locator('#assist-explain').click()
                expect(page.locator('#assist-result')).to_be_visible()
                page.keyboard.press('Escape')
                expect(page.locator('#assist-panel')).to_be_hidden()
                # A real single-word click anchors the popup and automatically explains.
                page.locator('#paragraph-1 p').scroll_into_view_if_needed()
                point = page.locator('#paragraph-1 p').evaluate("""p => {
                    const r = document.createRange(); r.setStart(p.firstChild, 0); r.setEnd(p.firstChild, 7);
                    const b = r.getBoundingClientRect(); return {x:b.x + b.width/2, y:b.y + b.height/2}; }""")
                click_scroll = page.evaluate('scrollY')
                page.mouse.click(point['x'], point['y'])
                expect(page.locator('#assist-result')).to_be_visible()
                expect(page.locator('#assist-selection')).to_have_text('Bonjour')
                self.assertEqual(page.evaluate('scrollY'), click_scroll)
                self.assertEqual(page.locator('#assist-selection').text_content(), 'Bonjour')
                page.locator('#assist-close').click()
                before = page.locator('#paragraph-1 p').text_content()
                page.get_by_role('button', name='Pronunciation hints', exact=True).click()
                expect(page.locator('#paragraph-1 .phonetic-word')).to_have_count(3)
                self.assertEqual(page.locator('#paragraph-1 p').text_content(), before)
                page.get_by_role('button', name='Hide hints', exact=True).click()
                self.assertEqual(page.locator('#paragraph-1 p').text_content(), before)
                page.mouse.click(315, 10)
                expect(page.locator('#assist-panel')).to_be_hidden()
                # Actual backend route, without fixture interception, handles missing key.
                context.unroute('**/assist/**', provider_fixture)
                result = page.evaluate("""async (id) => { const r = await fetch('/assist/explain/', {
                    method:'POST', headers:{'Content-Type':'application/json',
                    'X-CSRFToken':document.querySelector('#assistance-root input').value},
                    body:JSON.stringify({media_id:id,paragraph:0,start:7,end:10,locale:'fr-FR',explanation_locale:'en'})});
                    return {status:r.status, data:await r.json()}; }""", item.pk)
                self.assertEqual(result['status'], 503)
                self.assertEqual(result['data']['error']['code'], 'not_configured')
                page.evaluate('() => { navigator.mediaDevices.getUserMedia = window.captureAllowed; }')
                page.locator('#assist-open').click()
                page.locator('#assist-practice').click()
                page.locator('#practice-record').click()
                expect(page.locator('#practice-status')).to_contain_text('Recording locally')
                stopped_before = page.evaluate("Number(localStorage.getItem('qa-stopped-tracks') || 0)")
                page.get_by_role('button', name='Log out', exact=True).click()
                expect(page).to_have_url(self.live_server_url + '/')
                self.assertGreater(page.evaluate("Number(localStorage.getItem('qa-stopped-tracks') || 0)"), stopped_before)
                self.assertFalse(errors, errors)
            finally:
                browser.close()
