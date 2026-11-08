import json
from functools import wraps

from django.conf import settings
from django.core.exceptions import RequestDataTooBig, TooManyFieldsSent, TooManyFilesSent
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.csrf import csrf_failure as django_csrf_failure

from . import provider
from .contracts import AssistanceError, reference, validate_wav
from .limits import allowance


def error(code, message, status):
    return JsonResponse({'error': {'code': code, 'message': message}}, status=status)


def csrf_failure(request, reason=''):
    if request.path.startswith('/assist/'):
        response = error('csrf_failed', 'Reload the page and try again.', 403)
        response['Cache-Control'] = 'no-store, private'
        return response
    return django_csrf_failure(request, reason=reason)


def endpoint(view):
    @wraps(view)
    def guarded(request):
        response = None
        try:
            if request.method != 'POST':
                raise AssistanceError('post_required', 'Use POST for assistant requests.', 400)
            if not request.user.is_authenticated:
                raise AssistanceError('authentication_required', 'Sign in to use assistance.', 401)
            response = view(request)
        except AssistanceError as exc:
            response = error(exc.code, exc.message, exc.status)
        except (RequestDataTooBig, TooManyFieldsSent, TooManyFilesSent):
            response = error('request_too_large', 'The assistant request is too large.', 413)
        finally:
            # Django normally closes uploads at response cleanup; eagerly close on
            # every path too. No uploaded audio is persisted by this application.
            files = getattr(request, '_files', None)
            if files is not None:
                for _, uploads in files.lists():
                    for upload in uploads:
                        upload.close()
        if response is not None:
            response['Cache-Control'] = 'no-store, private'
            response['X-Content-Type-Options'] = 'nosniff'
        return response
    return csrf_protect(guarded)


def json_reference(request, max_chars=300):
    if request.content_type != 'application/json':
        raise AssistanceError('invalid_request', 'Send the selection as JSON.')
    if len(request.body) > 8192:
        raise AssistanceError('request_too_large', 'The selection request is too large.', 413)
    try:
        return reference(json.loads(request.body), max_chars=max_chars)
    except (ValueError, UnicodeDecodeError):
        raise AssistanceError('invalid_request', 'Send valid selection JSON.') from None


@endpoint
def explain(request):
    selected = json_reference(request, max_chars=1500)
    provider.configuration('TEXT')
    with allowance(request.user.pk):
        return JsonResponse(provider.explain(selected))


@endpoint
def lookup(request):
    selected = json_reference(request)
    provider.configuration('LOOKUP')
    with allowance(request.user.pk):
        return JsonResponse(provider.lookup(selected))


@endpoint
def sentence(request):
    selected = json_reference(request, max_chars=1500)
    provider.configuration('LOOKUP')
    with allowance(request.user.pk):
        return JsonResponse(provider.lookup(selected))


@endpoint
def phonetics(request):
    selected = json_reference(request, max_chars=1500)
    provider.configuration('LOOKUP')
    with allowance(request.user.pk):
        return JsonResponse(provider.phonetics(selected))


@endpoint
def pronounce(request):
    selected = json_reference(request, max_chars=1500)
    provider.configuration('TTS')
    with allowance(request.user.pk):
        return HttpResponse(provider.pronounce(selected), content_type='audio/wav')


@endpoint
def practice(request):
    if not (getattr(settings, 'GEMINI_VOICE_INPUT_ENABLED', False)
            and getattr(settings, 'GEMINI_VOICE_INPUT_APPROVED', False)):
        raise AssistanceError('voice_disabled', 'Voice analysis is not enabled for this app.', 503)
    provider.configuration('AUDIO')
    if request.content_type != 'multipart/form-data':
        raise AssistanceError('invalid_request', 'Send a WAV recording with its passage reference.')
    try:
        content_length = int(request.META.get('CONTENT_LENGTH') or 0)
    except (ValueError, TypeError):
        raise AssistanceError('invalid_request', 'Invalid upload size.') from None
    if content_length > 5 * 1024 * 1024 + 16384:
        raise AssistanceError('clip_too_large', 'Record at most 60 seconds and 5 MiB.', 413)
    selected = reference(request.POST.dict(), max_chars=1500)
    upload = request.FILES.get('audio')
    if upload is None or len(request.FILES) != 1 or len(request.FILES.getlist('audio')) != 1:
        raise AssistanceError('invalid_audio', 'Include exactly one WAV recording.')
    if upload.content_type not in ('audio/wav', 'audio/wave', 'audio/x-wav'):
        raise AssistanceError('invalid_audio', 'Only mono PCM WAV recordings are supported.')
    if upload.size > 5 * 1024 * 1024:
        raise AssistanceError('clip_too_large', 'Record at most 60 seconds and 5 MiB.', 413)
    audio = validate_wav(upload.read(5 * 1024 * 1024 + 1))
    with allowance(request.user.pk):
        return JsonResponse(provider.practice(selected, audio))
