#!/bin/sh
# Vercel's Django preset runs collectstatic after this command and serves it on CDN.
set -eu
cd "$(dirname "$0")/.."
python -c 'import sys; assert sys.version_info[:2] == (3, 12), "Python 3.12 is required"'
python -m pip install --force-reinstall --require-hashes -r requirements.txt
python manage.py check
# No migrate or seed here: previews must never change the shared Neon schema.
