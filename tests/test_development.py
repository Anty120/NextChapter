import json
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from nextchapter.development import configure_runserver


class DevelopmentBootstrapTests(SimpleTestCase):
    @patch('nextchapter.development.subprocess.run')
    def test_only_development_runserver_fetches_settings(self, run):
        for argv, env in [(['manage.py', 'migrate'], {}), (['manage.py', 'test'], {}),
                          (['manage.py', 'runserver'], {'APP_ENV': 'production'}),
                          (['manage.py', 'runserver'], {'GEMINI_ENABLED': 'false'})]:
            self.assertIsNone(configure_runserver(argv, env))
        run.assert_not_called()

    @patch('nextchapter.development.shutil.which', return_value='doppler')
    @patch('nextchapter.development.subprocess.run')
    def test_scoped_injection_preserves_overrides_and_local_database(self, run, which):
        data = {'GEMINI_API_KEY': 'not-a-real-key', 'GEMINI_ENABLED': 'true',
            'GEMINI_TEXT_MODEL': 'text', 'GEMINI_TTS_MODEL': 'tts', 'GEMINI_AUDIO_MODEL': 'audio',
            'DATABASE_URL': 'private-remote-database', 'DJANGO_SECRET_KEY': 'private-other-secret'}
        run.return_value = SimpleNamespace(returncode=0, stdout=json.dumps(data))
        env = {'GEMINI_TEXT_MODEL': 'my-explicit-model'}
        diagnostic = configure_runserver(['manage.py', 'runserver'], env)
        self.assertEqual(env['GEMINI_API_KEY'], 'not-a-real-key')
        self.assertEqual(env['GEMINI_TEXT_MODEL'], 'my-explicit-model')
        self.assertNotIn('DATABASE_URL', env)
        self.assertNotIn('DJANGO_SECRET_KEY', env)
        self.assertNotIn('not-a-real-key', diagnostic)
        self.assertIn('loaded', diagnostic)

    @patch('nextchapter.development.shutil.which', return_value='doppler')
    @patch('nextchapter.development.subprocess.run')
    def test_failed_authentication_is_actionable_without_echoing_provider_output(self, run, which):
        run.return_value = SimpleNamespace(returncode=1, stdout='private-token', stderr='private-token')
        result = configure_runserver(['manage.py', 'runserver'], {})
        self.assertIn('doppler login', result)
        self.assertNotIn('private-token', result)
