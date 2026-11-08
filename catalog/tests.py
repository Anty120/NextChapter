from io import StringIO
from pathlib import Path

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from catalog.library import get_media_metadata, validate_audio

from .models import Club, Comment, MediaItem, Membership, ReadingProgress, Report


class DemoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', stdout=StringIO())
        cls.user = get_user_model().objects.create_user('reader', password='a-test-only-password-293')
        cls.other = get_user_model().objects.create_user('other', password='another-test-password-719')
        cls.story = MediaItem.objects.get(slug='la-panaderia')
        cls.audio = MediaItem.objects.get(slug='audiobook-en-01')
        cls.club = Club.objects.get(slug='the-morning-pages')

    def test_seed_twice_preserves_identity_and_user_activity(self):
        ids = list(MediaItem.objects.values_list('pk', flat=True))
        Membership.objects.create(user=self.user, club=self.club)
        Comment.objects.create(user=self.user, club=self.club, body='A favorite place.')
        ReadingProgress.objects.create(user=self.user, media=self.story, paragraph=2)
        Report.objects.create(reporter=self.user, media=self.story, reason='Please review.')
        call_command('seed_demo', stdout=StringIO())
        call_command('seed_demo', stdout=StringIO())
        self.assertEqual(list(MediaItem.objects.values_list('pk', flat=True)), ids)
        self.assertEqual(Club.objects.count(), 4)
        self.assertEqual(Membership.objects.count(), 1)
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(ReadingProgress.objects.get().paragraph, 2)
        self.assertEqual(Report.objects.count(), 1)
        self.assertFalse(get_user_model().objects.filter(is_superuser=True).exists())

    def test_catalog_filters_combine_and_have_useful_empty_state(self):
        response = self.client.get('/', {'language': 'Spanish', 'format': 'story', 'level': 'A1'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['items']), 3)
        self.assertContains(response, self.story.title)
        self.assertNotContains(response, self.audio.title)
        response = self.client.get('/', {'language': 'French', 'format': 'audiobook'})
        self.assertContains(response, 'No media matches these filters')
        self.assertContains(response, 'Explore the full shelf')

    def test_media_text_credits_context_and_playable_audio_asset(self):
        response = self.client.get(self.story.get_absolute_url())
        self.assertContains(response, self.story.paragraphs[0])
        self.assertContains(response, self.story.cultural_context)
        self.assertContains(response, 'Credits &amp; source')
        response = self.client.get(self.audio.get_absolute_url())
        self.assertContains(response, '<audio', html=False)
        self.assertContains(response, 'controls preload="metadata"')
        self.assertContains(response, staticfiles_storage.url(self.audio.audio_file))
        metadata = get_media_metadata(self.audio.slug)
        self.assertContains(response, f'type="{metadata["audio_mime"]}"')
        data = (Path(__file__).parent / 'static' / self.audio.audio_file).read_bytes()
        validate_audio(data, metadata['audio_mime'], self.audio.audio_file)
        self.assertGreater(metadata['duration_seconds'], 10)
        self.assertTrue(any(data))

    def test_anonymous_reads_and_authentication_required_for_writes(self):
        for url in ('/', reverse('club_list'), self.club.get_absolute_url(), self.story.get_absolute_url()):
            self.assertEqual(self.client.get(url).status_code, 200)
        for name, pk in (('club_membership', self.club.pk), ('add_comment', self.club.pk), ('save_progress', self.story.pk)):
            self.assertEqual(self.client.post(reverse(name, args=[pk]), {}).status_code, 302)
        self.assertEqual(Membership.objects.count(), 0)
        self.assertEqual(Comment.objects.count(), 0)
        self.assertEqual(ReadingProgress.objects.count(), 0)

    @override_settings(WHITENOISE_USE_FINDERS=True)
    def test_bundled_audio_supports_byte_ranges_for_native_seeking(self):
        url = '/static/' + self.audio.audio_file
        response = self.client.get(url, HTTP_RANGE='bytes=0-63')
        self.assertEqual(response.status_code, 206)
        self.assertTrue(response['Content-Range'].startswith('bytes 0-63/'))
        content = b''.join(response.streaming_content)
        self.assertEqual(len(content), 64)
        metadata = get_media_metadata(self.audio.slug)
        self.assertEqual(response['Content-Type'], metadata['audio_mime'])
        source = (Path(__file__).parent / 'static' / self.audio.audio_file).read_bytes()
        validate_audio(source, metadata['audio_mime'], self.audio.audio_file)
        self.assertEqual(content, source[:64])
        self.assertEqual(self.client.get(url, HTTP_RANGE='bytes=99999999-').status_code, 416)

    def test_join_comment_refresh_and_leave_permissions(self):
        self.client.force_login(self.user)
        comment_url = reverse('add_comment', args=[self.club.pk])
        member_url = reverse('club_membership', args=[self.club.pk])
        self.assertEqual(self.client.post(comment_url, {'body': 'Not yet'}).status_code, 403)
        self.client.post(member_url, {'action': 'join'})
        self.client.post(member_url, {'action': 'join'})
        self.assertEqual(Membership.objects.filter(user=self.user, club=self.club).count(), 1)
        self.client.post(comment_url, {'body': 'A lovely story.', 'user': self.other.pk, 'club': 999})
        comment = Comment.objects.get()
        self.assertEqual(comment.user, self.user)
        self.assertEqual(comment.club, self.club)
        response = self.client.get(self.club.get_absolute_url())
        self.assertContains(response, 'A lovely story.')
        self.assertContains(response, "You're a member", html=False)
        self.client.post(member_url, {'action': 'leave'})
        self.assertFalse(Membership.objects.filter(user=self.user).exists())
        self.assertEqual(self.client.post(comment_url, {'body': 'No longer a member'}).status_code, 403)
        self.assertEqual(Comment.objects.count(), 1)

    def test_csrf_and_get_cannot_mutate_or_logout(self):
        self.client.force_login(self.user)
        for name, pk in (('club_membership', self.club.pk), ('add_comment', self.club.pk), ('save_progress', self.story.pk)):
            self.assertEqual(self.client.get(reverse(name, args=[pk])).status_code, 405)
        self.assertEqual(self.client.get(reverse('logout')).status_code, 405)
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)
        urls = [reverse('club_membership', args=[self.club.pk]), reverse('add_comment', args=[self.club.pk]),
                reverse('save_progress', args=[self.story.pk]), reverse('report', args=['media', self.story.pk]), reverse('logout')]
        for url in urls:
            self.assertEqual(csrf_client.post(url, {'action': 'join', 'body': 'Hello', 'reason': 'Review'}).status_code, 403)

    def test_invalid_comments_and_spoilers_escape_html(self):
        self.client.force_login(self.user)
        Membership.objects.create(user=self.user, club=self.club)
        url = reverse('add_comment', args=[self.club.pk])
        self.assertEqual(self.client.post(url, {'body': '  '}).status_code, 400)
        self.client.post(url, {'body': '<script>alert(1)</script>', 'spoiler': 'on'})
        response = self.client.get(self.club.get_absolute_url())
        self.assertContains(response, '&lt;script&gt;')
        self.assertContains(response, 'Contains spoilers')
        self.assertNotContains(response, '<script>alert(1)</script>')

    def test_new_comment_is_visible_after_refresh_when_older_comments_fill_a_page(self):
        Membership.objects.create(user=self.user, club=self.club)
        Comment.objects.bulk_create([
            Comment(user=self.other, club=self.club, body=f'Older thought {number}') for number in range(25)
        ])
        self.client.force_login(self.user)
        self.client.post(reverse('add_comment', args=[self.club.pk]), {'body': 'My new contribution'})
        response = self.client.get(self.club.get_absolute_url())
        self.assertContains(response, 'My new contribution')
        self.assertEqual(len(response.context['comments']), 20)
        self.assertEqual(Comment.objects.count(), 26)

    def test_resume_is_persistent_private_and_validated(self):
        self.client.force_login(self.user)
        story_url = reverse('save_progress', args=[self.story.pk])
        self.assertRedirects(self.client.post(story_url, {'paragraph': 2}), self.story.get_absolute_url() + '#paragraph-2')
        response = self.client.get(self.story.get_absolute_url())
        self.assertContains(response, 'saved-paragraph')
        self.assertEqual(response.context['progress'].paragraph, 2)
        for value in (-1, 999, 'not-a-number'):
            self.assertEqual(self.client.post(story_url, {'paragraph': value}).status_code, 400)
        audio_url = reverse('save_progress', args=[self.audio.pk])
        self.assertEqual(self.client.post(audio_url, {'seconds': 12.5}, HTTP_ACCEPT='application/json').json(), {'saved': True})
        self.client.post(audio_url, {'seconds': 18.2})
        self.assertEqual(ReadingProgress.objects.filter(user=self.user, media=self.audio).count(), 1)
        self.assertEqual(self.client.get(self.audio.get_absolute_url()).context['progress'].seconds, 18.2)
        for value in (-1, 'nan', 'inf', 86401, 'bad'):
            self.assertEqual(self.client.post(audio_url, {'seconds': value}).status_code, 400)
        self.client.force_login(self.other)
        self.assertIsNone(self.client.get(self.story.get_absolute_url()).context['progress'])

    def test_reports_are_admin_reviewable_and_require_exactly_one_target(self):
        self.client.force_login(self.user)
        url = reverse('report', args=['media', self.story.pk])
        self.assertEqual(self.client.post(url, {'reason': ' '}).status_code, 400)
        self.client.post(url, {'reason': 'Please check the attribution.', 'reporter': self.other.pk, 'status': 'resolved'})
        report = Report.objects.get()
        self.assertEqual(report.reporter, self.user)
        self.assertEqual(report.status, Report.Status.OPEN)
        self.assertEqual(report.media, self.story)
        comment = Comment.objects.create(user=self.other, club=self.club, body='A comment')
        self.client.post(reverse('report', args=['comment', comment.pk]), {'reason': 'Please review this comment.'})
        self.assertEqual(Report.objects.count(), 2)
        staff = get_user_model().objects.create_superuser('moderator', password='test-only-admin-password-791')
        self.client.force_login(staff)
        self.assertContains(self.client.get(reverse('admin:catalog_report_changelist')), 'Please check the attribution.')
        with self.assertRaises(IntegrityError), transaction.atomic():
            Report.objects.create(reporter=self.user, reason='No target')
        with self.assertRaises(IntegrityError), transaction.atomic():
            Report.objects.create(reporter=self.user, reason='Two targets', media=self.story, comment=comment)

    def test_drafts_are_hidden_and_admin_models_registered(self):
        self.story.published = False
        self.story.save()
        self.assertNotContains(self.client.get('/'), self.story.title)
        self.assertEqual(self.client.get(self.story.get_absolute_url()).status_code, 404)
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(reverse('save_progress', args=[self.story.pk]), {'paragraph': 0}).status_code, 404)
        self.assertEqual(self.client.get(reverse('report', args=['media', self.story.pk])).status_code, 404)
        for model in (MediaItem, Club, Membership, Comment, ReadingProgress, Report):
            self.assertTrue(admin.site.is_registered(model))

    def test_signup_login_and_post_logout(self):
        response = self.client.post(reverse('signup'), {'username': 'new-reader', 'password1': 'a-unique-test-password-813', 'password2': 'a-unique-test-password-813'})
        self.assertRedirects(response, reverse('login'))
        self.assertTrue(self.client.login(username='new-reader', password='a-unique-test-password-813'))
        self.assertRedirects(self.client.post(reverse('logout')), '/')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_story_language_applies_only_to_prose(self):
        self.client.force_login(self.user)
        for language, code in (('Spanish', 'es'), ('French', 'fr')):
            story = MediaItem.objects.filter(language=language, format='story').first()
            with self.subTest(language=language):
                response = self.client.get(story.get_absolute_url())
                self.assertContains(response, '<div class="story-text">')
                self.assertContains(response, f'<p lang="{code}">{story.paragraphs[0]}</p>', html=True)
                self.assertContains(response, 'aria-label="Save my place at paragraph 1"')
                self.assertNotContains(response, f'<div class="story-text" lang="{code}">')
                self.assertContains(response, '<html lang="en">')

    def test_failed_login_explains_errors_and_marks_credentials_invalid(self):
        response = self.client.post(reverse('login'), {'username': 'reader', 'password': 'wrong-password'})
        self.assertContains(response, 'id="login-errors" class="error" role="alert"')
        self.assertContains(response, 'Check your username and password, then try logging in again.')
        self.assertContains(response, 'aria-invalid="true" aria-describedby="login-errors"', count=2)
        self.assertContains(response, 'value="reader"')
        self.assertNotContains(response, 'value="wrong-password"')
        self.assertContains(response, '<label for="id_username">Username:</label>', html=True)
        self.assertContains(response, '<label for="id_password">Password:</label>', html=True)

    def test_login_required_field_errors_and_initial_form(self):
        response = self.client.post(reverse('login'), {'username': 'reader'})
        self.assertContains(response, 'Password: This field is required.')
        self.assertContains(response, 'aria-invalid="true" aria-describedby="login-errors"', count=1)
        response = self.client.get(reverse('login'), {'next': '/media/1/'})
        self.assertNotContains(response, 'role="alert"')
        self.assertNotContains(response, 'aria-invalid=')
        self.assertContains(response, 'name="next" value="/media/1/"')
