"""Club contract and real controller tests using isolated, explicitly fake media.

The integrated seed/asset validation is owned by #12/#27; these fixtures never
claim to establish completeness, playback, or rights for the real media pack.
"""
import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from catalog.models import Club, Comment, MediaItem, Membership


MANIFEST = Path(__file__).resolve().parents[1] / 'catalog/demo_library/clubs.json'


@override_settings(STORAGES={
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
})
class ClubLibraryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.records = json.loads(MANIFEST.read_text(encoding='utf-8'))['clubs']
        cls.reader = get_user_model().objects.create_user(username='club-reader')
        cls.other = get_user_model().objects.create_user(username='another-reader')
        formats = {
            'la-panaderia': ('story', 'Spanish'),
            'book-es-01': ('book', 'Spanish'),
            'audiobook-es-01': ('audiobook', 'Spanish'),
            'song-en-01': ('song', 'English'),
        }
        cls.clubs = []
        for record in cls.records:
            slug = record['featured_media_slug']
            media_format, language = formats[slug]
            media = MediaItem.objects.create(
                slug=slug, title=f'Fixture {slug}', creator='Test fixture',
                language=language, format=media_format, level='C1',
                text='Isolated fixture paragraph.\n\nAnother fixture paragraph.',
                description='Isolated test media, not the real library asset.',
                attribution='Test fixture only.', cultural_context='Test fixture.',
                audio_file='catalog/audio/fixture.wav' if media_format in ('song', 'audiobook') else '',
                published=True,
            )
            cls.clubs.append(Club.objects.create(
                **{key: record[key] for key in ('slug', 'name', 'language', 'description')},
                featured_media=media,
            ))

    def test_manifest_contract_and_no_fake_activity(self):
        manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
        self.assertEqual(manifest['schema_version'], 1)
        self.assertEqual({record['slug']: record['featured_media_slug'] for record in self.records}, {
            'the-morning-pages': 'la-panaderia', 'demo-book-club': 'book-es-01',
            'demo-audio-club': 'audiobook-es-01', 'demo-song-club': 'song-en-01',
        })
        self.assertEqual(len(self.records), 4)
        for record in self.records:
            self.assertEqual(set(record), {'slug', 'name', 'language', 'description', 'featured_media_slug'})
            self.assertIn('all levels welcome', record['description'].lower())
            self.assertIn('?', record['description'])
            self.assertLessEqual(len(record['name']), 160)
        self.assertEqual(Membership.objects.count(), 0)
        self.assertEqual(Comment.objects.count(), 0)

    def test_public_discovery_and_each_featured_destination(self):
        response = self.client.get(reverse('club_list'))
        self.assertContains(response, 'catalog/clubs.css')
        for club in self.clubs:
            with self.subTest(club=club.slug):
                self.assertContains(response, club.name)
                self.assertContains(response, club.get_absolute_url())
                self.assertContains(response, club.featured_media.get_absolute_url())
                detail = self.client.get(club.get_absolute_url())
                self.assertContains(detail, club.featured_media.get_format_display())
                self.assertContains(detail, club.featured_media.title)
                self.assertContains(detail, club.featured_media.get_absolute_url())
                self.assertContains(detail, club.description)
                self.assertContains(detail, 'Log in to join')
                self.assertNotContains(detail, 'name="body"')
                self.assertEqual(self.client.get(club.featured_media.get_absolute_url()).status_code, 200)

    def test_membership_comment_refresh_leave_for_every_club(self):
        self.client.force_login(self.reader)
        for club in self.clubs:
            with self.subTest(club=club.slug):
                membership = reverse('club_membership', args=[club.pk])
                post = reverse('add_comment', args=[club.pk])
                self.assertContains(self.client.get(club.get_absolute_url()), 'browsing as a nonmember')
                self.assertEqual(self.client.post(post, {'body': 'Before joining'}).status_code, 403)
                for _ in range(2):
                    self.assertRedirects(self.client.post(membership, {'action': 'join'}), club.get_absolute_url())
                self.assertEqual(Membership.objects.filter(user=self.reader, club=club).count(), 1)
                detail = self.client.get(club.get_absolute_url())
                self.assertContains(detail, "You're a member", html=False)
                self.assertContains(detail, '<label for="id_body">', html=False)
                self.assertContains(detail, 'csrfmiddlewaretoken')
                body = f'A real test reflection for {club.slug}'
                self.assertRedirects(self.client.post(post, {
                    'body': body, 'spoiler': 'on', 'user': self.other.pk, 'club': self.clubs[-1].pk,
                }), club.get_absolute_url())
                comment = Comment.objects.get(club=club, body=body)
                self.assertEqual(comment.user, self.reader)
                refreshed = self.client.get(club.get_absolute_url())
                self.assertContains(refreshed, body)
                self.assertContains(refreshed, 'Contains spoilers')
                self.assertContains(refreshed, reverse('report', args=['comment', comment.pk]))
                self.assertRedirects(self.client.post(membership, {'action': 'leave'}), club.get_absolute_url())
                self.assertFalse(Membership.objects.filter(user=self.reader, club=club).exists())
                left = self.client.get(club.get_absolute_url())
                self.assertContains(left, body)
                self.assertNotContains(left, 'name="body"')
                self.assertEqual(self.client.post(post, {'body': 'After leaving'}).status_code, 403)
                self.assertEqual(Comment.objects.filter(club=club).count(), 1)

    def test_anonymous_and_nonmember_cannot_post(self):
        club = self.clubs[0]
        post = reverse('add_comment', args=[club.pk])
        self.assertEqual(self.client.post(post, {'body': 'Anonymous'}).status_code, 302)
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(post, {'body': 'Not a member'}).status_code, 403)
        self.assertEqual(Comment.objects.count(), 0)

    def test_csrf_enforced_for_membership_and_comments(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.reader)
        club = self.clubs[0]
        membership = reverse('club_membership', args=[club.pk])
        post = reverse('add_comment', args=[club.pk])
        self.assertEqual(client.post(membership, {'action': 'join'}).status_code, 403)
        client.get(club.get_absolute_url())
        token = client.cookies['csrftoken'].value
        self.assertEqual(client.post(membership, {'action': 'join', 'csrfmiddlewaretoken': token}).status_code, 302)
        self.assertEqual(client.post(post, {'body': 'Missing token'}).status_code, 403)
        self.assertEqual(client.post(post, {'body': 'With token', 'csrfmiddlewaretoken': token}).status_code, 302)

    def test_new_comment_is_visible_after_post_with_pagination(self):
        club = self.clubs[0]
        Comment.objects.bulk_create([
            Comment(club=club, user=self.other, body=f'Older reflection {i}') for i in range(23)
        ])
        self.client.force_login(self.reader)
        Membership.objects.create(user=self.reader, club=club)
        response = self.client.post(reverse('add_comment', args=[club.pk]), {'body': 'Newest reflection'}, follow=True)
        self.assertContains(response, 'Newest reflection')
        self.assertContains(response, 'Comment pages')
        self.assertContains(response, '?page=2')
        self.assertEqual(len(response.context['comments']), 20)
        second = self.client.get(club.get_absolute_url(), {'page': 2})
        self.assertEqual(len(second.context['comments']), 4)
        self.assertNotContains(second, 'Newest reflection')

    def test_invalid_comment_keeps_error_and_membership(self):
        self.client.force_login(self.reader)
        club = self.clubs[0]
        Membership.objects.create(user=self.reader, club=club)
        response = self.client.post(reverse('add_comment', args=[club.pk]), {'body': ''})
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, 'This field is required.', status_code=400)
        self.assertContains(response, 'csrfmiddlewaretoken', status_code=400)
        self.assertEqual(Comment.objects.count(), 0)

    def test_unpublished_featured_media_is_not_linked(self):
        club = self.clubs[0]
        media = club.featured_media
        media.published = False
        media.save(update_fields=['published'])
        for url in (reverse('club_list'), club.get_absolute_url()):
            response = self.client.get(url)
            self.assertNotContains(response, media.title)
            self.assertNotContains(response, media.get_absolute_url())
