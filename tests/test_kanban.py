"""Offline checks for dispatch gates; never create real GitHub reservations."""
import json
import unittest
from unittest.mock import patch

from scripts import kanban


class ClaimGateTests(unittest.TestCase):
    number = 27

    def task(self, body='Depends-on: none'):
        return {'html_url': f'https://github.com/{kanban.REPO}/issues/{self.number}', 'body': body}

    def board(self, status='Ready', attached=True):
        return json.dumps({'items': [{'content': {'url': self.task()['html_url']}, 'status': status}]
                           if attached else []})

    def test_only_ready_attached_issues_are_claimable(self):
        for status in ('Backlog', 'Blocked', 'In Progress', 'Review', 'Done', None):
            with self.subTest(status=status), patch.object(kanban, 'run', return_value=self.board(status)):
                with self.assertRaises(RuntimeError):
                    kanban.require_ready(self.number, self.task())
        with patch.object(kanban, 'run', return_value=self.board(attached=False)):
            with self.assertRaises(RuntimeError):
                kanban.require_ready(self.number, self.task())

    def test_missing_malformed_or_duplicate_dependency_declarations_fail(self):
        for body in ('', 'Depends-on: later', 'Depends-on: #3 or #4',
                     'Depends-on: none\nDepends-on: #3', 'Depends-on: #27'):
            with self.subTest(body=body), patch.object(kanban, 'run', return_value=self.board()):
                with self.assertRaises(RuntimeError):
                    kanban.require_ready(self.number, self.task(body))

    def test_explicit_no_dependencies_needs_no_dependency_api_calls(self):
        with patch.object(kanban, 'run', return_value=self.board()), patch.object(kanban, 'api') as api:
            kanban.require_ready(self.number, self.task())
            api.assert_not_called()

    def test_open_cancelled_and_pr_dependencies_fail(self):
        for value in ({'state': 'open'}, {'state': 'closed', 'state_reason': 'not_planned'},
                      {'state': 'closed', 'state_reason': 'completed', 'pull_request': {}}):
            with self.subTest(value=value), patch.object(kanban, 'run', return_value=self.board()), \
                    patch.object(kanban, 'api', return_value=value):
                with self.assertRaises(RuntimeError):
                    kanban.require_ready(self.number, self.task('Depends-on: #3'))

    def test_all_dependencies_must_be_completed(self):
        with patch.object(kanban, 'run', return_value=self.board()), \
                patch.object(kanban, 'api', return_value={'state': 'closed', 'state_reason': 'completed'}) as api:
            kanban.require_ready(self.number, self.task('Depends-on: #3, #4'))
            self.assertEqual({call.args[0] for call in api.call_args_list},
                             {f'repos/{kanban.REPO}/issues/3', f'repos/{kanban.REPO}/issues/4'})

    def test_board_failure_stops_before_any_claim_mutation(self):
        with patch.object(kanban, 'issue', return_value=self.task()), \
                patch.object(kanban, 'run', side_effect=RuntimeError('board access denied')), \
                patch.object(kanban, 'api') as api:
            with self.assertRaises(RuntimeError):
                kanban.claim(self.number, 'offline-test')
            api.assert_not_called()

    def test_not_ready_stops_before_any_claim_mutation(self):
        with patch.object(kanban, 'issue', return_value=self.task()), \
                patch.object(kanban, 'run', return_value=self.board('Blocked')), \
                patch.object(kanban, 'api') as api:
            with self.assertRaises(RuntimeError):
                kanban.claim(self.number, 'offline-test')
            api.assert_not_called()
