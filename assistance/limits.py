"""Atomic cache counters contain user IDs/counts only, never selections or speech.

Use a shared Django cache for budgets across multiple application processes.
"""
import time
from contextlib import contextmanager

from django.conf import settings
from django.core.cache import cache

from .contracts import AssistanceError


@contextmanager
def allowance(user_id):
    if getattr(settings, 'APP_ENV', 'development') == 'production':
        backend = settings.CACHES['default']['BACKEND']
        if not any(name in backend for name in ('RedisCache', 'PyMemcacheCache', 'PyLibMCCache')):
            raise AssistanceError('limits_unavailable', 'AI assistance needs a shared rate-limit cache in production.', 503)
    timeout = max(1, min(45, int(getattr(settings, 'GEMINI_TIMEOUT_SECONDS', 20))))
    minute = int(time.time()) // 60
    key = f'assistance:rate:{user_id}:{minute}'
    lease = f'assistance:active:{user_id}'
    try:
        cache.add(key, 0, 120)
        count = cache.incr(key)
        if count > int(getattr(settings, 'GEMINI_RATE_LIMIT', 12)):
            raise AssistanceError('rate_limited', 'Please wait a minute before trying again.', 429)
        # Single in-flight request per user. Atomic add avoids get/set races.
        if not cache.add(lease, True, timeout + 30):
            raise AssistanceError('busy', 'Wait for your current assistant request to finish.', 429)
    except AssistanceError:
        raise
    except Exception:
        raise AssistanceError('limits_unavailable', 'The assistant is temporarily unavailable.', 503) from None
    try:
        yield
    finally:
        try:
            cache.delete(lease)
        except Exception:
            pass  # The bounded lease expires; do not expose speech in a debug error.
