"""Offline checks: no Vercel login, provider credentials, or remote database."""
import json
import os
from pathlib import Path
import subprocess
import sys

from django.test import SimpleTestCase


ROOT = Path(__file__).resolve().parent.parent


class VercelConfigTests(SimpleTestCase):
    def test_django_preset_and_resolved_wsgi_function(self):
        config = json.loads((ROOT / 'vercel.json').read_text())
        self.assertEqual(config['$schema'], 'https://openapi.vercel.sh/vercel.json')
        self.assertEqual(config['framework'], 'django')
        self.assertEqual(config['buildCommand'], 'sh scripts/vercel_build.sh')
        self.assertNotIn('builds', config)  # Do not bypass the Django/static preset.
        self.assertNotIn('routes', config)
        self.assertNotIn('rewrites', config)
        function = config['functions']['nextchapter/wsgi.py']
        self.assertIsInstance(function['maxDuration'], int)
        self.assertGreater(function['maxDuration'], 0)
        self.assertLessEqual(function['maxDuration'], 60)
        self.assertEqual((ROOT / '.python-version').read_text().strip(), '3.12')
        self.assertTrue((ROOT / 'scripts/vercel_build.sh').is_file())

    def test_python_entry_serves_wsgi_health_without_credentials(self):
        env = {key: value for key, value in os.environ.items()
               if not key.startswith(('DJANGO_', 'APP_', 'DATABASE_', 'VERCEL_'))}
        env.update(APP_ENV='test', DJANGO_DEBUG='false', DATABASE_URL='',
                   DJANGO_SECRET_KEY='offline-test-fixture-not-a-production-secret',
                   DJANGO_ALLOWED_HOSTS='testserver', DJANGO_SSL_REDIRECT='false')
        script = '''
from wsgiref.util import setup_testing_defaults
from django.conf import settings
from index import app, application
from nextchapter.wsgi import application as django_application
assert app is application is django_application
assert settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3'
environ = {}
setup_testing_defaults(environ)
environ.update(PATH_INFO='/health/', HTTP_HOST='testserver')
result = {}
def start_response(status, headers, exc_info=None):
    result['status'] = status
response = application(environ, start_response)
try:
    body = b''.join(response)
finally:
    response.close()
assert result['status'] == '200 OK', result
assert b'"status": "ok"' in body, body
'''
        result = subprocess.run([sys.executable, '-c', script], cwd=ROOT,
                                env=env, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
