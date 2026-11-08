"""Explicit small live checks using public demo text and generated reference audio."""
import io
import json
import time
import wave

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from assistance import provider
from assistance.contracts import AssistanceError, reference


class Command(BaseCommand):
    help = ('Make live Gemini text/TTS requests for a published passage. Optional audio '
            'check analyzes generated reference speech, never personal microphone input. '
            'Requests consume the configured provider quota. No pronunciation-quality claim.')

    def add_arguments(self, parser):
        parser.add_argument('--media-id', required=True, type=int)
        parser.add_argument('--paragraph', default=0, type=int)
        parser.add_argument('--start', required=True, type=int)
        parser.add_argument('--end', required=True, type=int)
        parser.add_argument('--locale', required=True)
        parser.add_argument('--include-audio', action='store_true')

    def handle(self, **options):
        try:
            selected = reference({**options, 'explanation_locale': 'en'})
            if options['include_audio'] and not (settings.GEMINI_VOICE_INPUT_ENABLED and settings.GEMINI_VOICE_INPUT_APPROVED):
                raise CommandError('Enable and approve the configured voice service before its live check.')
            # Disable optional reference caching so each receipt represents a real request.
            from django.test.utils import override_settings
            with override_settings(GEMINI_CACHE_TTL_SECONDS=0):
                started = time.monotonic()
                text = provider.explain(selected)
                self.stdout.write(json.dumps({'path': 'text', 'model': settings.GEMINI_TEXT_MODEL,
                    'status': 'ok', 'seconds': round(time.monotonic() - started, 2),
                    'meaning_present': bool(text['meaning']), 'ipa_present': bool(text['ipa'])}))
                started = time.monotonic()
                speech = provider.pronounce(selected)
                with wave.open(io.BytesIO(speech), 'rb') as audio:
                    duration = audio.getnframes() / audio.getframerate()
                self.stdout.write(json.dumps({'path': 'tts', 'model': settings.GEMINI_TTS_MODEL,
                    'status': 'ok', 'seconds': round(time.monotonic() - started, 2),
                    'audio_seconds': round(duration, 2), 'bytes': len(speech)}))
                if options['include_audio']:
                    if duration > 15:
                        raise CommandError('Generated reference exceeds the 15-second practice bound; choose a shorter selection.')
                    started = time.monotonic()
                    result = provider.practice(selected, speech)
                    self.stdout.write(json.dumps({'path': 'audio', 'model': settings.GEMINI_AUDIO_MODEL,
                        'status': 'ok', 'seconds': round(time.monotonic() - started, 2),
                        'transcript_present': bool(result['transcript']),
                        'assessment_supported': result['assessment_supported'],
                        'input': 'generated public reference; not a personal attempt or quality benchmark'}))
        except AssistanceError as exc:
            raise CommandError(f'{exc.code} (HTTP {exc.status}). No provider body or secret logged.') from None
