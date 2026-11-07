"""Exercise environment selection in fresh processes without opening a database."""
import json
import os
import subprocess
import sys

from django.test import SimpleTestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.db import transaction


class DatabaseConfigurationTests(SimpleTestCase):
    def load_database(self, url=None):
        env = os.environ.copy()
        env.pop('DATABASE_URL', None)
        if url is not None:
            env['DATABASE_URL'] = url
        return subprocess.run(
            [sys.executable, '-c',
             'import json; from nextchapter.settings import DATABASES; '
             'print(json.dumps(DATABASES["default"], default=str))'],
            env=env, capture_output=True, text=True, timeout=10,
        )

    def test_absent_and_blank_url_keep_sqlite(self):
        for url in (None, '', '   '):
            with self.subTest(url=url):
                result = self.load_database(url)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)['ENGINE'], 'django.db.backends.sqlite3')

    def test_postgres_url_decodes_credentials_and_requires_tls(self):
        for scheme in ('postgres', 'postgresql'):
            result = self.load_database(
                f'{scheme}://reader:p%40ss%3Aword@demo-pooler.example/db%2Dname?sslmode=disable'
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            config = json.loads(result.stdout)
            self.assertEqual(config['ENGINE'], 'django.db.backends.postgresql')
            self.assertEqual(config['NAME'], 'db-name')
            self.assertEqual(config['PASSWORD'], 'p@ss:word')
            self.assertEqual(config['HOST'], 'demo-pooler.example')
            self.assertEqual(config['OPTIONS']['sslmode'], 'require')
            self.assertEqual(config['CONN_MAX_AGE'], 0)
            self.assertTrue(config['DISABLE_SERVER_SIDE_CURSORS'])

    def test_invalid_url_fails_without_exposing_credentials(self):
        for url in ('mysql://user:private-marker@host/db',
                    'postgres://user:private-marker@host:bad/db',
                    'postgres://user:private-marker@host/',
                    'postgres://user:private-marker@/db'):
            with self.subTest(url=url):
                result = self.load_database(url)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('DATABASE_URL must be a valid PostgreSQL URL', result.stderr)
                self.assertNotIn('private-marker', result.stderr)

    def test_stronger_certificate_verification_is_preserved(self):
        result = self.load_database('postgresql://user:fixture@host/db?sslmode=verify-full')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['OPTIONS']['sslmode'], 'verify-full')


class DatabaseTransactionTests(TransactionTestCase):
    def test_create_read_delete_and_multi_write_rollback(self):
        users = get_user_model().objects
        user = users.create_user(username='database-proof')
        self.assertEqual(users.get(pk=user.pk).username, 'database-proof')
        user.delete()
        self.assertFalse(users.filter(username='database-proof').exists())
        with self.assertRaisesMessage(RuntimeError, 'deliberate rollback'):
            with transaction.atomic():
                users.create_user(username='rollback-first')
                users.create_user(username='rollback-second')
                self.assertEqual(users.filter(username__startswith='rollback-').count(), 2)
                raise RuntimeError('deliberate rollback')
        self.assertFalse(users.filter(username__startswith='rollback-').exists())
