"""Small, cache-free probes for deployment verification."""
from django.conf import settings
from django.db import DatabaseError, connections
from django.http import JsonResponse
from django.views.decorators.http import require_safe


def response(payload, status=200):
    result = JsonResponse(payload, status=status)
    result['Cache-Control'] = 'no-store'
    return result


@require_safe
def health(request):
    """Process liveness; does not claim database readiness."""
    return response({'status': 'ok', 'release': settings.APP_RELEASE})


@require_safe
def readiness(request):
    """Verify the configured database answers without writing any records."""
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute('SELECT 1')
            if cursor.fetchone() != (1,):
                return response({'status': 'unavailable'}, status=503)
    except DatabaseError:
        return response({'status': 'unavailable'}, status=503)
    return response({'status': 'ready', 'release': settings.APP_RELEASE})
