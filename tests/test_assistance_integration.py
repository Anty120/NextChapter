import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings

from catalog.models import MediaItem
from tests.test_assistance import explanation


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
        self.assertContains(response, '/static/assistance/panel.js')
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
