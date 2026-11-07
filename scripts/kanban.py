#!/usr/bin/env python3
"""Shared GitHub kanban and exclusive task claims. Requires Python 3, git, gh."""
import argparse
import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone

REPO = 'Anty120/NextChapter'
PROJECT = 'PVT_kwHOBJujSM4Bqo-f'
OWNER = 'kvn8888'
NUMBER = '7'


def run(*args, data=None):
    result = subprocess.run(args, input=data, text=True, capture_output=True, timeout=60)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout


def api(path, payload=None):
    args = ['gh', 'api', path]
    if payload is not None:
        args += ['--method', 'POST', '--input', '-']
    return json.loads(run(*args, data=json.dumps(payload) if payload is not None else None))


def issue(number):
    value = api(f'repos/{REPO}/issues/{number}')
    if 'pull_request' in value or value['state'] != 'open':
        raise RuntimeError('Choose an open issue, not a pull request or closed issue.')
    return value


def set_status(number, status):
    fields = json.loads(run('gh', 'project', 'field-list', NUMBER, '--owner', OWNER, '--format', 'json'))
    field = next(f for f in fields['fields'] if f['name'] == 'Status')
    option = next(o['id'] for o in field['options'] if o['name'] == status)
    item = json.loads(run('gh', 'project', 'item-add', NUMBER, '--owner', OWNER,
                         '--url', f'https://github.com/{REPO}/issues/{number}', '--format', 'json'))
    run('gh', 'project', 'item-edit', '--id', item['id'], '--project-id', PROJECT,
        '--field-id', field['id'], '--single-select-option-id', option)


def ref_path(number):
    return f'heads/agent-claims/issue-{number}'


def current_claim(number):
    ref = api(f'repos/{REPO}/git/ref/{ref_path(number)}')
    commit = api(f'repos/{REPO}/git/commits/{ref["object"]["sha"]}')
    return ref['object']['sha'], json.loads(commit['message'])


def comment(number, body):
    api(f'repos/{REPO}/issues/{number}/comments', {'body': body})


def claim(number, agent):
    issue(number)
    login = api('user')['login']
    repo = api(f'repos/{REPO}')
    base = api(f'repos/{REPO}/git/ref/heads/{repo["default_branch"]}')['object']['sha']
    tree = api(f'repos/{REPO}/git/commits/{base}')['tree']['sha']
    metadata = {'issue': number, 'agent': agent, 'user': login, 'session': str(uuid.uuid4()),
                'started': datetime.now(timezone.utc).isoformat()}
    # Unique commit: even two agents on one account have different claim identities.
    commit = api(f'repos/{REPO}/git/commits',
                 {'message': json.dumps(metadata), 'tree': tree, 'parents': [base]})['sha']
    # GitHub creates this ref only if absent. Any failure stops before task work.
    try:
        api(f'repos/{REPO}/git/refs', {'ref': 'refs/' + ref_path(number), 'sha': commit})
    except RuntimeError as error:
        raise RuntimeError('Claim denied or could not be confirmed. Do not start work. '
                           'Run the show command to inspect an existing claim. ' + str(error)) from error
    print(json.dumps({'claim': commit, **metadata}), flush=True)
    try:
        api(f'repos/{REPO}/issues/{number}/assignees', {'assignees': [login]})
        set_status(number, 'In Progress')
        comment(number, f'Claimed by @{login}, agent `{agent}`.\n\nClaim: `{commit}`\n'
                       f'Started: {metadata["started"]}\n\nWork branch: `work/issue-{number}-{commit[:8]}`')
    except RuntimeError as error:
        raise RuntimeError(f'Task is reserved by claim {commit}, but board/comment sync failed. '
                           'Do not claim again. Repair access and update the card, or release this claim. '
                           + str(error)) from error


def verify_claim(number, expected):
    sha, metadata = current_claim(number)
    if sha != expected:
        raise RuntimeError('Claim does not match. Do not alter another agent\'s task.')
    if metadata['user'] != api('user')['login']:
        raise RuntimeError('Use the GitHub account that created this claim.')
    return sha, metadata


def delete_claim(number, sha):
    # Compare-and-delete: an old session cannot remove a newer claim.
    ref = 'refs/' + ref_path(number)
    run('git', '-c', 'credential.helper=', '-c', 'credential.helper=!gh auth git-credential',
        'push', f'--force-with-lease={ref}:{sha}', f'https://github.com/{REPO}.git', ':' + ref)


def handoff(number, expected, status, note):
    sha, metadata = verify_claim(number, expected)
    # Leave the lock in place on any partial failure; retry with the same claim SHA.
    set_status(number, status)
    comment(number, f'Agent `{metadata["agent"]}` handing off claim `{sha}` to **{status}**.\n\n{note}')
    delete_claim(number, sha)
    print(json.dumps({'issue': number, 'status': status, 'released': sha}))


def release(number, expected):
    sha, _ = verify_claim(number, expected)
    delete_claim(number, sha)
    print(json.dumps({'issue': number, 'released': sha,
                      'warning': 'Reservation released without changing the board. Update the issue and board manually.'}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    take = commands.add_parser('claim', help='Reserve an issue before editing')
    take.add_argument('issue', type=int)
    take.add_argument('--agent', required=True, help='Distinct agent/session name; avoid private machine details')
    show = commands.add_parser('show', help='Read the current task reservation')
    show.add_argument('issue', type=int)
    add = commands.add_parser('add', help='Add an existing issue to the board')
    add.add_argument('issue', type=int)
    give = commands.add_parser('handoff', help='Record progress and release your reservation')
    give.add_argument('issue', type=int)
    give.add_argument('--claim', required=True, help='Full claim SHA returned when claiming')
    give.add_argument('--status', required=True, choices=['Ready', 'Review', 'Blocked', 'Done'])
    give.add_argument('--note', required=True, help='Evidence, remaining work, next owner, and PR URL when relevant')
    recover = commands.add_parser('release', help='Release your reservation when board sync is unavailable')
    recover.add_argument('issue', type=int)
    recover.add_argument('--claim', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'claim':
            claim(args.issue, args.agent)
        elif args.command == 'show':
            sha, metadata = current_claim(args.issue)
            print(json.dumps({'claim': sha, **metadata}, indent=2))
        elif args.command == 'add':
            issue(args.issue)
            item = run('gh', 'project', 'item-add', NUMBER, '--owner', OWNER,
                       '--url', f'https://github.com/{REPO}/issues/{args.issue}', '--format', 'json')
            print(item)
        elif args.command == 'release':
            release(args.issue, args.claim)
        else:
            handoff(args.issue, args.claim, args.status, args.note)
    except (RuntimeError, subprocess.TimeoutExpired, KeyError, ValueError, StopIteration) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
