import os
import subprocess
import sys
from unittest.mock import patch

from django.db import OperationalError
from django.test import SimpleTestCase, TestCase, override_settings


class HealthTests(SimpleTestCase):
    @override_settings(APP_RELEASE='test-commit')
    def test_liveness_reports_release_without_database(self):
        response = self.client.get('/health/')
        self.assertEqual(response.json(), {'status': 'ok', 'release': 'test-commit'})
        self.assertEqual(response['Cache-Control'], 'no-store')

    def test_readiness_failure_is_503_without_error_details(self):
        with patch('nextchapter.health.connections') as connections:
            connections.__getitem__.return_value.cursor.side_effect = OperationalError('private-database-details')
            response = self.client.get('/ready/')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {'status': 'unavailable'})
        self.assertNotContains(response, 'private-database-details', status_code=503)

    def test_probe_rejects_writes(self):
        self.assertEqual(self.client.post('/health/').status_code, 405)
        self.assertEqual(self.client.post('/ready/').status_code, 405)


class DatabaseReadinessTests(TestCase):
    def test_configured_isolated_database_is_ready(self):
        response = self.client.get('/ready/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ready')


class ProductionSettingsTests(SimpleTestCase):
    def load_settings(self, **changes):
        env = {key: value for key, value in os.environ.items()
               if not key.startswith(('DJANGO_', 'APP_ENV'))}
        env.update(APP_ENV='production', DJANGO_DEBUG='false', DJANGO_ALLOWED_HOSTS='demo.example.com',
                   DJANGO_SECRET_KEY='test-only-configuration-key-' * 3)
        for key, value in changes.items():
            if value is None:
                env.pop(key, None)
            else:
                env[key] = value
        return subprocess.run([sys.executable, '-c', 'import nextchapter.settings'],
                              env=env, capture_output=True, text=True, timeout=10)

    def test_production_requires_injected_key(self):
        result = self.load_settings(DJANGO_SECRET_KEY=None)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('DJANGO_SECRET_KEY is required', result.stderr)

    def test_production_refuses_debug_and_wildcard_hosts(self):
        for changes in ({'DJANGO_DEBUG': 'true'}, {'DJANGO_ALLOWED_HOSTS': '*'},
                        {'DJANGO_ALLOWED_HOSTS': ''}):
            with self.subTest(changes=changes):
                self.assertNotEqual(self.load_settings(**changes).returncode, 0)

    def test_production_accepts_explicit_configuration(self):
        self.assertEqual(self.load_settings().returncode, 0)
