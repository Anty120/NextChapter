"""Local runserver bootstrap. WSGI, builds and management writes never fetch secrets."""
import json
import os
from pathlib import Path
import shutil
import subprocess


ASSISTANCE_KEYS = (
    'GEMINI_API_KEY', 'GEMINI_ENABLED', 'GEMINI_TEXT_MODEL', 'GEMINI_TTS_MODEL',
    'GEMINI_AUDIO_MODEL', 'GEMINI_VOICE_INPUT_ENABLED', 'GEMINI_VOICE_INPUT_APPROVED',
    'GEMINI_TIMEOUT_SECONDS', 'GEMINI_RATE_LIMIT', 'GEMINI_CACHE_TTL_SECONDS',
)


def configure_runserver(argv, environ=None, root=None):
    """Load only Gemini settings from the already-authorized local Doppler CLI.

    Explicit process settings win. No key is written to disk or printed. In
    particular, development startup never imports a shared DATABASE_URL.
    """
    env = os.environ if environ is None else environ
    if (len(argv) < 2 or argv[1] != 'runserver'
            or env.get('APP_ENV', 'development') != 'development'
            or env.get('GEMINI_ENABLED', '').lower() in {'false', '0'}):
        return None
    required = ('GEMINI_API_KEY', 'GEMINI_TEXT_MODEL', 'GEMINI_TTS_MODEL', 'GEMINI_AUDIO_MODEL', 'GEMINI_ENABLED')
    if all(env.get(name) for name in required):
        return None
    base = Path(root) if root else Path(__file__).resolve().parent.parent
    executable = shutil.which('doppler')
    if not executable:
        local = base / '.venv' / 'doppler' / ('doppler.exe' if os.name == 'nt' else 'doppler')
        if local.is_file():
            executable = str(local)
    if not executable:
        return 'Word help: Doppler CLI was not found. Install/sign in to Doppler, or inject the GEMINI_* backend settings before starting runserver.'
    try:
        result = subprocess.run([
            executable, 'secrets', 'download', '--project', env.get('DOPPLER_PROJECT', 'hack-coms-hackathon'),
            '--config', env.get('DOPPLER_CONFIG', 'dev'), '--no-file', '--format', 'json', '--no-check-version',
        ], capture_output=True, text=True, timeout=10)
        if result.returncode:
            return 'Word help: Doppler could not load development settings. Run doppler login, then restart runserver.'
        data = json.loads(result.stdout)
        if not isinstance(data, dict):
            raise ValueError
        for name in ASSISTANCE_KEYS:
            value = data.get(name)
            if isinstance(value, str) and value:
                env.setdefault(name, value)
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return 'Word help: development settings could not be loaded. Check Doppler access, then restart runserver.'
    if not all(env.get(name) for name in required):
        return 'Word help: Gemini settings are incomplete in the selected Doppler config. Check GEMINI_API_KEY, GEMINI_ENABLED and the three model IDs.'
    return 'Word help: development Gemini settings loaded from Doppler (no database settings imported).'
