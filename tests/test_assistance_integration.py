import json
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command, CommandError
from django.test import TestCase, override_settings
from django.templatetags.static import static

from catalog.models import MediaItem
from tests.test_assistance import explanation, wav
from assistance.contracts import AssistanceError


@override_settings(APP_ENV='test', GEMINI_ENABLED=True, GEMINI_API_KEY='test-only-key',
                   GEMINI_TEXT_MODEL='test-text', GEMINI_CACHE_TTL_SECONDS=0,
                   CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
class AssistanceIntegrationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.item = MediaItem.objects.create(slug='integration', title='A book',
            language='French', text='Pour moi, un livre.', published=True)
        self.user = get_user_model().objects.create_user('integration')
        self.client.force_login(self.user)
        self.reference = {'media_id': self.item.pk, 'paragraph': 0, 'start': 5,
            'end': 8, 'locale': 'fr-FR', 'explanation_locale': 'en'}

    def post(self):
        return self.client.post('/assist/explain/', json.dumps(self.reference), content_type='application/json')

    @override_settings(GEMINI_ENABLED=False)
    def test_reader_works_without_assistance_and_never_exposes_secret(self):
        response = self.client.get(f'/media/{self.item.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pour moi, un livre.')
        self.assertContains(response, 'data-enabled="false"')
        self.assertNotContains(response, 'test-only-key')
        self.assertContains(response, static('assistance/panel.js'))
        self.assertEqual(self.post().status_code, 503)

    @patch('assistance.provider.generate')
    def test_zero_ttl_disables_cache_on_real_application_routes(self, generate):
        generate.return_value = [{'text': json.dumps(explanation())}]
        for _ in range(2):
            response = self.post()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['selection'], 'moi')
        self.assertEqual(generate.call_count, 2)

    @override_settings(APP_ENV='production')
    @patch('assistance.provider.generate')
    def test_production_rejects_process_local_budget(self, generate):
        response = self.post()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['error']['code'], 'limits_unavailable')
        generate.assert_not_called()

    @patch('assistance.provider.pronounce', return_value=wav())
    @patch('assistance.provider.explain', return_value={**explanation(), 'meaning': 'do not log passage'})
    def test_live_check_command_prints_receipts_without_content_or_key(self, explain, pronounce):
        output = StringIO()
        call_command('check_gemini', media_id=self.item.pk, start=5, end=8, locale='fr-FR', stdout=output)
        receipts = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual([r['path'] for r in receipts], ['text', 'tts'])
        self.assertNotIn('test-only-key', output.getvalue())
        self.assertNotIn('do not log passage', output.getvalue())
        self.assertEqual(explain.call_args.args[0]['selection'], 'moi')

    @patch('assistance.provider.explain', side_effect=AssistanceError('provider_quota', 'private detail', 429))
    def test_live_check_command_failure_does_not_echo_provider_body(self, explain):
        with self.assertRaisesMessage(CommandError, 'provider_quota (HTTP 429)') as caught:
            call_command('check_gemini', media_id=self.item.pk, start=5, end=8, locale='fr-FR', stdout=StringIO())
        self.assertNotIn('private detail', str(caught.exception))
