"""Optional local browser rehearsal: pip install playwright; python tests/browser_demo.py --channel msedge.

Uses a running local demo, creates a uniquely named reader, and writes screenshots
to an ignored directory. Not part of the Django unit suite; no production access.
"""
import argparse
from html import escape
from pathlib import Path
from uuid import uuid4

from playwright.sync_api import expect, sync_playwright


def check_metadata_restore(page, base_url):
    """Exercise both metadata orders explicitly, independent of cache timing."""
    audio_url = page.locator('audio source').evaluate('(source) => source.src')
    script_url = page.locator('script[src$="/player.js"]').evaluate('(script) => script.src')
    fixture = page.context.new_page()
    fixture.goto(base_url)
    for metadata_first in (True, False):
        preload = 'metadata' if metadata_first else 'none'
        fixture.set_content(
            f'<audio id="player" preload="{preload}" data-seconds="17" '
            f'src="{escape(audio_url, quote=True)}"></audio>'
            '<p id="audio-error" hidden></p>'
        )
        if metadata_first:
            fixture.wait_for_function('document.querySelector("audio").readyState >= 1')
        else:
            assert fixture.locator('audio').evaluate('(audio) => audio.readyState') == 0
        fixture.add_script_tag(url=script_url)
        if not metadata_first:
            fixture.locator('audio').evaluate('(audio) => audio.load()')
        fixture.wait_for_function('Math.abs(document.querySelector("audio").currentTime - 17) < 0.1')
        assert fixture.locator('audio').evaluate('(audio) => audio.paused'), 'Restore must not autoplay'
    fixture.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default='http://127.0.0.1:8000')
    parser.add_argument('--channel', default=None)
    parser.add_argument('--output', default='.venv/qa')
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    username = 'rehearsal-' + uuid4().hex[:12]
    password = 'Rehearsal-only-' + uuid4().hex
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel=args.channel, headless=True)
        context = browser.new_context(viewport={'width': 1440, 'height': 1050})
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(args.base_url)
        expect(page.get_by_role('heading', name='Your next chapter starts here.')).to_be_visible()
        page.keyboard.press('Tab')
        expect(page.get_by_role('link', name='Skip to content')).to_be_focused()
        page.keyboard.press('Enter')
        expect(page.locator('main')).to_be_focused()
        page.get_by_role('heading', name='Your next chapter starts here.').click()
        page.screenshot(path=str(output / 'catalog-desktop.png'), full_page=True)
        page.get_by_role('combobox', name='Language', exact=True).select_option('Spanish')
        page.get_by_role('combobox', name='Format', exact=True).select_option('story')
        page.get_by_role('combobox', name='Approx. level', exact=True).select_option('A1')
        page.get_by_role('button', name='Find a story').click()
        expect(page.locator('.book-card')).to_have_count(3)
        page.get_by_role('combobox', name='Approx. level', exact=True).select_option('C2')
        page.get_by_role('button', name='Find a story').click()
        expect(page.get_by_text('No media matches these filters.', exact=False)).to_be_visible()
        page.get_by_role('link', name='Explore the full shelf').click()

        page.get_by_role('link', name='Join us').click()
        page.get_by_label('Username:', exact=True).fill(username)
        page.get_by_label('Password:', exact=True).fill(password)
        page.get_by_label('Password confirmation:', exact=True).fill(password)
        page.get_by_role('button', name='Create account').click()
        page.get_by_label('Username:', exact=True).fill(username)
        page.get_by_label('Password:', exact=True).fill(password)
        page.get_by_role('button', name='Log in', exact=False).click()
        story = page.get_by_role('link').filter(has=page.get_by_role('heading', name='La panadería de la calle Sol', exact=True))
        story_path = story.get_attribute('href')
        story.click()
        page.get_by_role('button', name='Save my place at paragraph 3', exact=True).press('Enter')
        page.reload()
        expect(page.locator('#paragraph-2')).to_have_class('paragraph saved-paragraph')
        page.screenshot(path=str(output / 'reader-desktop.png'), full_page=True)
        page.get_by_role('link', name='Shelf', exact=True).click()
        expect(page.get_by_role('link', name='Resume')).to_have_attribute('href', story_path + '#paragraph-2')

        page.get_by_role('link', name='Clubs', exact=True).click()
        page.get_by_role('link', name='Meet the club').click()
        page.get_by_role('button', name='Join this club').press('Enter')
        comment_text = 'This bakery reminds me of mornings with my family. ' + username
        page.get_by_label('Your comment:', exact=True).fill(comment_text)
        page.get_by_label('Contains spoilers', exact=False).check()
        page.get_by_role('button', name='Post comment').press('Enter')
        page.reload()
        expect(page.get_by_text("You're a member", exact=False)).to_be_visible()
        comment = page.locator('.comment').filter(has_text=comment_text)
        comment.get_by_text('Contains spoilers · show comment', exact=True).click()
        expect(comment.get_by_text(comment_text, exact=True)).to_be_visible()
        comment.get_by_role('link', name='Report comment', exact=True).click()
        page.get_by_label('What should a moderator review?', exact=False).fill('Browser rehearsal: please review this example.')
        page.get_by_role('button', name='Send report').press('Enter')
        expect(page.get_by_text('Report received.', exact=False)).to_be_visible()
        club_url = page.url

        page.get_by_role('link', name='Shelf', exact=True).click()
        recording = page.get_by_role('link').filter(has=page.get_by_role('heading', name='The Blue Door', exact=True))
        audio_path = recording.get_attribute('href')
        recording.click()
        audio = page.locator('audio')
        page.wait_for_function('document.querySelector("audio").readyState >= 2')
        audio.click(position={'x': 25, 'y': 25})
        page.wait_for_function('document.querySelector("audio").currentTime > 1')
        page.evaluate('document.querySelector("audio").currentTime = 9')
        audio.click(position={'x': 25, 'y': 25})
        expect(page.locator('#save-status')).to_have_text('Your listening position is saved.')
        page.wait_for_function('Number(document.querySelector("#audio-seconds").value) >= 9')
        page.reload()
        page.wait_for_function('document.querySelector("audio").currentTime >= 8')
        assert page.locator('audio').evaluate('(audio) => audio.paused'), 'Resume must not autoplay'

        # Keep the pause-before-seek sequence working alongside the original native-control sequence.
        audio.evaluate('(audio) => audio.pause()')
        with page.expect_response(lambda response: response.request.method == 'POST'
                                  and response.url.endswith('/progress/')) as saved:
            audio.evaluate('(audio) => { audio.currentTime = 12; }')
        assert saved.value.ok
        expect(page.locator('#save-status')).to_have_text('Your listening position is saved.')
        page.reload()
        page.wait_for_function('Math.abs(document.querySelector("audio").currentTime - 12) < 0.1')
        assert page.locator('audio').evaluate('(audio) => audio.paused'), 'Paused seek must not autoplay'
        check_metadata_restore(page, args.base_url)

        for width in (390, 320):
            page.set_viewport_size({'width': width, 'height': 844})
            for path in ('/', story_path, audio_path, '/clubs/', club_url, '/accounts/login/'):
                page.goto(path if path.startswith('http') else args.base_url + path)
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), f'Overflow at {width}px: {path}'
            page.goto(args.base_url)
            page.screenshot(path=str(output / f'catalog-mobile-{width}.png'), full_page=True)
        page.goto(club_url)
        page.screenshot(path=str(output / 'club-mobile.png'), full_page=True)
        page.get_by_role('button', name='Leave club').click()
        expect(page.get_by_role('button', name='Join this club')).to_be_visible()
        expect(page.get_by_label('Your comment:', exact=True)).to_have_count(0)
        page.get_by_role('button', name='Log out', exact=True).press('Enter')
        expect(page.get_by_role('link', name='Log in', exact=True)).to_be_visible()
        assert not errors, errors
        browser.close()
    print('PASS: filters, signup/login/logout, keyboard actions, reader resume, membership/comments, report, actual audio playback/resume, pause-before-seek, both metadata loading orders without autoplay, 390/320px overflow checks, no browser errors.')
    print(f'Screenshots: {output.resolve()}')


if __name__ == '__main__':
    main()
