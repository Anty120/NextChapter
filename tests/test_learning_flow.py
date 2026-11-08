import json
from io import StringIO
from unittest.mock import patch

from django.core.cache import cache
from django.core.management import call_command
from django.test import Client, TestCase, override_settings

from assistance import provider
from assistance.contracts import validate_wav
from catalog.models import MediaItem, ReadingProgress
from catalog.quizzes import book_quiz
from tests import test_assistance as helpers

wav = helpers.wav


@override_settings(ROOT_URLCONF='tests.test_assistance', GEMINI_ENABLED=True, GEMINI_API_KEY='test-key-only',
                   GEMINI_TEXT_MODEL='test-text', GEMINI_TTS_MODEL='test-tts', GEMINI_AUDIO_MODEL='test-audio',
                   GEMINI_VOICE_INPUT_ENABLED=True, GEMINI_VOICE_INPUT_APPROVED=True,
                   CSRF_FAILURE_VIEW='assistance.views.csrf_failure', APP_ENV='test',
                   CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
class FastLookupTests(TestCase):
    setUp = helpers.AssistanceTests.setUp
    @override_settings(GEMINI_LOOKUP_MODEL='fast-test')
    @patch('assistance.provider.generate')
    def test_small_lookup_cached_separately_from_full_explanation(self, generate):
        generate.return_value = [{'text': json.dumps(dict(translation='Hello', meaning='Greeting', ipa='bɔ̃ʒuʁ', approximation='bon-ZHOOR'))}]
        for _ in range(2):
            response = self.client.post('/assist/lookup/', self.ref, content_type='application/json')
            self.assertEqual(response.status_code, 200)
        self.assertEqual(generate.call_count, 1)
        self.assertEqual(generate.call_args.args[0], 'LOOKUP')
        self.assertEqual(generate.call_args.args[2]['maxOutputTokens'], 384)
        self.assertEqual(provider.configuration('LOOKUP')[1], 'fast-test')

    @patch('assistance.provider.generate')
    def test_phonetics_align_only_server_words_and_preserve_unicode(self, generate):
        generate.return_value = [{'text': json.dumps({'words': [{'ipa':'bɔ̃ʒuʁ','sound':'bon-ZHOOR'}]})}]
        result = self.client.post('/assist/phonetics/', self.ref, content_type='application/json')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()['words'][0], {'start':0,'end':7,'text':'Bonjour','ipa':'bɔ̃ʒuʁ','sound':'bon-ZHOOR'})
        cache.clear()
        generate.return_value = [{'text': '{"words": []}'}]
        self.assertEqual(self.client.post('/assist/phonetics/', self.ref, content_type='application/json').status_code, 502)

    @patch('assistance.provider.practice')
    def test_long_sentence_and_sixty_second_capture(self, practice):
        self.item.text = 'Bonjour ' * 50 + '.'
        self.item.save()
        ref = {**self.ref, 'start':0, 'end':len(self.item.text)}
        from django.core.files.uploadedfile import SimpleUploadedFile
        practice.return_value = {'transcript':'Synthetic test', 'feedback':[], 'assessment_supported':False}
        raw = wav(seconds=60, rate=24000)
        self.assertEqual(validate_wav(raw), raw)
        response = self.client.post('/assist/practice/', {**ref, 'audio':SimpleUploadedFile('sentence.wav', raw, content_type='audio/wav')})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(practice.call_args.args[0]['selection'], self.item.text)

    def test_new_routes_require_authentication_and_csrf(self):
        browser = Client(enforce_csrf_checks=True)
        browser.force_login(self.user)
        for route in ['lookup', 'sentence', 'phonetics']:
            with self.subTest(route=route):
                self.assertEqual(browser.post(f'/assist/{route}/', self.ref, content_type='application/json').status_code, 403)
                self.client.logout()
                self.assertEqual(self.client.post(f'/assist/{route}/', self.ref, content_type='application/json').status_code, 401)


class BookQuizTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', stdout=StringIO())

    def test_each_seeded_book_has_link_and_server_graded_quiz(self):
        for book in MediaItem.objects.filter(format='book', published=True):
            path = f'/media/{book.pk}/quiz/'
            self.assertContains(self.client.get(book.get_absolute_url()), path)
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, 'Answer:')
            questions = book_quiz(book.slug)
            self.assertEqual(len(questions), 5)
            answers = {f'q{i}':str(q['answer']) for i,q in enumerate(questions)}
            self.assertContains(self.client.post(path, answers), '5 of 5 correct')
            self.assertEqual(self.client.post(path, {'score':5,'q0':'999'}).status_code, 400)
            self.assertEqual(Client(enforce_csrf_checks=True).post(path, answers).status_code, 403)

    def test_drafts_nonbooks_and_unknown_banks_have_no_quiz(self):
        book = MediaItem.objects.get(slug='book-es-01')
        book.published = False; book.save()
        story = MediaItem.objects.get(slug='la-panaderia')
        for item in [book, story]:
            self.assertEqual(self.client.get(f'/media/{item.pk}/quiz/').status_code, 404)

    def test_seed_twice_retires_english_audio_and_preserves_activity(self):
        from django.contrib.auth import get_user_model
        user = get_user_model().objects.create_user('seed-preservation')
        old = MediaItem.objects.create(slug='song-en-01', title='Old English recording', language='English', format='song', published=True)
        ReadingProgress.objects.create(user=user, media=old, seconds=12)
        for _ in range(2):
            call_command('seed_demo', stdout=StringIO())
        old.refresh_from_db()
        self.assertFalse(old.published)
        self.assertEqual(ReadingProgress.objects.get(media=old).seconds, 12)
        audio = MediaItem.objects.filter(published=True, format__in=['song','audiobook'])
        self.assertEqual(audio.count(), 4)
        self.assertEqual(set(audio.values_list('language', flat=True)), {'French','Spanish'})
