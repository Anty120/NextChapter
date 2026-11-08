"""Local-only real Chrome rehearsal; install Playwright separately from app dependencies.

Run against the same checkout's local SQLite server. Creates unique local readers
and staff, never prints passwords, and saves screenshots plus machine evidence.
"""
import argparse
import json
import os
from pathlib import Path
import sys
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nextchapter.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
from catalog.library import get_media_metadata
from catalog.models import Club, MediaItem
from tests.test_media_experience import check_player_browser
from playwright.sync_api import expect, sync_playwright


def login(page, base, username, password):
    page.goto(base + '/accounts/login/')
    page.get_by_label('Username:', exact=True).fill(username)
    page.get_by_label('Password:', exact=True).fill(password)
    page.get_by_role('button', name='Log in', exact=False).press('Enter')


def keyboard_check(page):
    # Login autofocus and same-URL navigation can retain a focused field. Start
    # the sequential navigation check at the document boundary on every page.
    page.locator('body').evaluate('(body) => { body.tabIndex = -1; body.focus(); body.removeAttribute("tabindex"); }')
    page.keyboard.press('Tab')
    expect(page.get_by_role('link', name='Skip to content')).to_be_focused()
    page.keyboard.press('Enter')
    expect(page.locator('main')).to_be_focused()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default='http://127.0.0.1:8000')
    parser.add_argument('--channel', default='chrome')
    parser.add_argument('--output', default='.venv/qa')
    args = parser.parse_args()
    base = args.base_url.rstrip('/')
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    username = 'rehearsal-' + uuid4().hex[:12]
    password = 'Local-rehearsal-' + uuid4().hex
    staffname = 'staff-' + uuid4().hex[:12]
    staffpassword = uuid4().hex
    get_user_model().objects.create_superuser(staffname, password=staffpassword)
    othername = 'other-' + uuid4().hex[:12]
    get_user_model().objects.create_user(othername, password=password)
    # Playwright runs its sync API inside an event loop; read ORM data beforehand.
    story = MediaItem.objects.get(slug='la-panaderia')
    reading = [story] + list(MediaItem.objects.filter(format='book', published=True))
    audio_items = list(MediaItem.objects.filter(format__in=['audiobook', 'song'], published=True))
    clubs = list(Club.objects.all())
    evidence = {'formats': {}, 'books': [], 'audio': [], 'clubs': [], 'widths': [320, 390]}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel=args.channel, headless=True)
        evidence['browser'] = browser.version
        context = browser.new_context(viewport={'width': 1440, 'height': 1050})
        page = context.new_page()
        errors, failed_assets = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('response', lambda response: failed_assets.append(response.url)
                if '/static/' in response.url and response.status >= 400 else None)
        page.on('requestfailed', lambda request: failed_assets.append(request.url)
                if '/static/' in request.url and 'ERR_ABORTED' not in (request.failure or '') else None)
        page.goto(base)
        keyboard_check(page)
        page.screenshot(path=str(output / 'catalog-desktop.png'), full_page=True)
        # Format is a segmented radio group (was a select); check the option, then submit.
        for fmt, label, count in [('story', 'Short story', 6), ('book', 'Book', 2), ('audiobook', 'Audiobook', 2), ('song', 'Song', 2)]:
            page.goto(base)
            page.get_by_role('group', name='Format').get_by_role('radio', name=label, exact=True).check()
            page.get_by_role('button', name='Find a story').press('Enter')
            expect(page.locator('.book-card')).to_have_count(count)
            evidence['formats'][fmt] = count
        page.goto(base + '/?language=Spanish&format=story&level=A1')
        expect(page.locator('.book-card')).to_have_count(3)
        page.goto(base + '/?language=Spanish&format=story&level=C2')
        expect(page.get_by_text('No media matches these filters.', exact=False)).to_be_visible()
        page.get_by_role('link', name='Explore the full shelf').press('Enter')
        page.get_by_role('link', name='Join us').press('Enter')
        page.get_by_label('Username:', exact=True).fill(username)
        page.get_by_label('Password:', exact=True).fill(password)
        page.get_by_label('Password confirmation:', exact=True).fill(password)
        page.get_by_role('button', name='Create account').press('Enter')
        login(page, base, username, password)
        for item in reading:
            page.goto(base + item.get_absolute_url())
            keyboard_check(page)
            expect(page.locator('.story-text .paragraph')).to_have_count(len(item.paragraphs))
            if item.format == 'book':
                # The table of contents is a sheet opened from the reader bar's Chapters button.
                page.get_by_role('button', name='Chapters', exact=False).press('Enter')
                expect(page.get_by_role('navigation', name='Table of contents')).to_be_visible()
                expect(page.locator('.chapter-toc a')).to_have_count(len(get_media_metadata(item.slug)['chapters']))
                last = get_media_metadata(item.slug)['chapters'][-1]['start_paragraph']
                page.locator('.chapter-toc a').last.press('Enter')
                expect(page.locator(f'#paragraph-{last}')).to_be_focused()
            page.get_by_role('button', name='Save my place at paragraph 3', exact=True).press('Enter')
            # Bookmarks now save in place (fetch, no navigation); wait for the confirmation.
            expect(page.locator('#paragraph-2 .bookmark-label')).to_have_text('Saved here')
            page.reload()
            expect(page.locator('#paragraph-2')).to_have_class('paragraph saved-paragraph')
            page.screenshot(path=str(output / (item.slug + '.png')), full_page=False)
            evidence['books'].append({'slug': item.slug, 'paragraphs': len(item.paragraphs), 'bookmark': 2})
        for item in audio_items:
            metadata = get_media_metadata(item.slug)
            page.goto(base + item.get_absolute_url())
            keyboard_check(page)
            # The word-help practice panel adds its own <audio> elements; target the media player.
            audio = page.locator('audio#player')
            url = page.locator('audio#player source').evaluate('(source) => source.src')
            expect(page.locator('audio#player source')).to_have_attribute('type', metadata['audio_mime'])
            expect(page.get_by_text(metadata['performer'], exact=False).first).to_be_visible()
            expect(page.locator('.component-credit')).to_have_count(len(metadata['sources']))
            expect(page.locator('.story-text .paragraph')).to_have_count(len(item.paragraphs))
            if item.format == 'song':
                expect(page.get_by_text('Full lyrics not bundled.', exact=False).first).to_be_visible()
                assert page.locator('.component-credit a').count() >= 4
            else:
                expect(page.get_by_role('heading', name='Chapter transcript')).to_be_visible()
            response = context.request.get(url, headers={'Range': 'bytes=0-63'})
            assert response.status == 206
            assert response.headers['content-type'] == metadata['audio_mime']
            assert response.headers['content-range'].startswith('bytes 0-63/')
            assert len(response.body()) == 64
            page.wait_for_function('document.querySelector("audio").readyState >= 2')
            assert audio.evaluate('(a) => a.paused && !a.autoplay')
            # Keyboard focuses the native control; Space starts playback.
            audio.focus()
            page.keyboard.press('Space')
            page.wait_for_function('document.querySelector("audio").currentTime > 0.5')
            page.keyboard.press('Space')
            with page.expect_response(lambda r: r.request.method == 'POST' and r.url.endswith('/progress/')) as saved:
                audio.evaluate('(a) => { a.pause(); a.currentTime = 12; }')
            assert saved.value.ok
            expect(page.locator('#save-status')).to_have_text('Your listening position is saved.')
            page.reload()
            page.wait_for_function('Math.abs(document.querySelector("audio").currentTime - 12) < 0.1')
            assert audio.evaluate('(a) => a.paused && !a.autoplay')
            page.screenshot(path=str(output / (item.slug + '.png')), full_page=False)
            fixture = context.new_page()
            check_player_browser(fixture, base, url)
            fixture.close()
            evidence['audio'].append({'slug': item.slug, 'mime': metadata['audio_mime'], 'range': 206,
                                      'duration': metadata['duration_seconds'], 'resume': 12, 'autoplay': False})
        page.goto(base + '/clubs/')
        expect(page.locator('.club-card')).to_have_count(4)
        report_reason = 'Browser rehearsal report ' + username
        for index, club in enumerate(clubs):
            page.goto(base + club.get_absolute_url())
            keyboard_check(page)
            expect(page.get_by_label('Your comment:', exact=True)).to_have_count(0)
            # A nonmember cannot forge a comment even with their valid CSRF token.
            csrf = page.locator('[name=csrfmiddlewaretoken]').first.input_value()
            denied = context.request.post(base + f'/clubs/{club.pk}/comments/', form={'body': 'forged', 'csrfmiddlewaretoken': csrf})
            assert denied.status == 403
            denied = context.request.post(base + f'/clubs/{club.pk}/membership/', form={'action': 'join'})
            assert denied.status == 403
            page.get_by_role('button', name='Join this club', exact=False).press('Enter')
            text = f'A welcoming discussion in {club.name}. {username}'
            page.get_by_label('Your comment:', exact=True).fill(text)
            page.get_by_label('Contains spoilers', exact=False).check()
            page.get_by_role('button', name='Post comment', exact=False).press('Enter')
            page.reload()
            expect(page.get_by_text("You're a member", exact=False)).to_be_visible()
            comment = page.locator('.comment').filter(has_text=text)
            comment.locator('summary').press('Enter')
            expect(comment.get_by_text(text, exact=True)).to_be_visible()
            if index == 0:
                comment.get_by_role('link', name='Report comment', exact=True).press('Enter')
                page.get_by_label('What should a moderator review?', exact=False).fill(report_reason)
                page.get_by_role('button', name='Send report').press('Enter')
                expect(page.get_by_text('Report received.', exact=False)).to_be_visible()
            page.get_by_role('button', name='Leave club', exact=True).press('Enter')
            page.reload()
            expect(page.get_by_role('button', name='Join this club', exact=False)).to_be_visible()
            expect(page.get_by_label('Your comment:', exact=True)).to_have_count(0)
            assert page.locator('.comment').filter(has_text=text).count() == 1
            evidence['clubs'].append(club.slug)
        for width in (320, 390):
            page.set_viewport_size({'width': width, 'height': 844})
            paths = ['/', '/clubs/', '/accounts/login/'] + [i.get_absolute_url() for i in reading + audio_items] + [c.get_absolute_url() for c in clubs]
            for path in paths:
                page.goto(base + path)
                keyboard_check(page)
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), f'Overflow at {width}px: {path}'
            page.goto(base + '/clubs/')
            page.screenshot(path=str(output / f'clubs-{width}.png'), full_page=True)
            page.goto(base)
            page.screenshot(path=str(output / f'catalog-{width}.png'), full_page=True)
        # Log out lives in the account popover menu.
        page.get_by_role('button', name='account menu', exact=False).press('Enter')
        page.get_by_role('button', name='Log out', exact=True).press('Enter')
        expect(page.get_by_role('link', name='Log in', exact=True)).to_be_visible()
        csrf = next(cookie['value'] for cookie in context.cookies() if cookie['name'] == 'csrftoken')
        anon = context.request.post(base + f'/media/{story.pk}/progress/', form={'paragraph': '1'},
                                    headers={'X-CSRFToken': csrf}, max_redirects=0)
        assert anon.status == 302
        other = browser.new_context()
        private = other.new_page()
        login(private, base, othername, password)
        for item in reading:
            private.goto(base + item.get_absolute_url())
            expect(private.locator('.saved-paragraph')).to_have_count(0)
        for item in audio_items:
            private.goto(base + item.get_absolute_url())
            expect(private.locator('audio#player')).to_have_attribute('data-seconds', '0')
        other.close()
        staff = browser.new_context()
        admin = staff.new_page()
        admin.goto(base + '/admin/login/')
        admin.get_by_label('Username:', exact=True).fill(staffname)
        admin.get_by_label('Password:', exact=True).fill(staffpassword)
        admin.get_by_role('button', name='Log in', exact=True).press('Enter')
        admin.goto(base + '/admin/catalog/report/?q=' + username)
        expect(admin.locator('#result_list tbody tr')).to_have_count(1)
        admin.locator('#result_list tbody th a').click()
        expect(admin.locator('.field-reason .readonly')).to_have_text(report_reason)
        admin.get_by_label('Status:', exact=True).select_option('reviewed')
        admin.get_by_label('Review notes:', exact=True).fill('Local browser rehearsal reviewed.')
        admin.locator('input[name="_save"]').press('Enter')
        admin.goto(base + '/admin/catalog/report/?q=' + username)
        expect(admin.locator('#result_list .field-status')).to_have_text('Reviewed')
        staff.close()
        assert not errors, errors
        assert not failed_assets, failed_assets
        evidence.update({'errors': errors, 'failed_assets': failed_assets, 'staff_report_review': True,
                         'privacy': True, 'csrf_and_nonmember': True, 'keyboard': True,
                         'human_listening': False, 'screen_reader': False, 'physical_mobile': False})
        browser.close()
    (output / 'evidence.json').write_text(json.dumps(evidence, indent=2))
    print(json.dumps(evidence, indent=2))
    print(f'Screenshots: {output.resolve()}')


if __name__ == '__main__':
    main()
