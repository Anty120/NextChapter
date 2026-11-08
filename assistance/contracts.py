"""Bounded public contracts. Provider strings are data, never trusted markup."""
import io
from array import array
import re
import struct
import wave

from catalog.models import MediaItem


class AssistanceError(Exception):
    def __init__(self, code, message, status=400):
        self.code, self.message, self.status = code, message, status
        super().__init__(code)


LANGUAGES = {'English': 'en', 'French': 'fr', 'Spanish': 'es', 'German': 'de',
             'Italian': 'it', 'Portuguese': 'pt', 'Japanese': 'ja', 'Chinese': 'zh',
             'Arabic': 'ar', 'Hindi': 'hi', 'Korean': 'ko'}
LOCALE = re.compile(r'^[a-z]{2,3}(?:-[A-Za-z0-9]{2,8}){0,2}$')
TRANSLATION_LANGUAGES = (
    ('en', 'English'), ('fr', 'French'), ('es', 'Spanish'), ('de', 'German'),
    ('it', 'Italian'), ('pt', 'Portuguese'), ('ja', 'Japanese'), ('ko', 'Korean'),
    ('zh', 'Chinese'), ('ar', 'Arabic'), ('hi', 'Hindi'),
)


def reference(data, max_chars=300):
    if not isinstance(data, dict):
        raise AssistanceError('invalid_selection', 'Choose a word or sentence in published media.')
    numbers = []
    for name in ('media_id', 'paragraph', 'start', 'end'):
        value = data.get(name)
        if isinstance(value, bool) or not isinstance(value, (str, int)) or not re.fullmatch(r'[0-9]{1,12}', str(value)):
            raise AssistanceError('invalid_selection', 'Selection positions must be nonnegative integers.')
        numbers.append(int(value))
    media_id, paragraph, start, end = numbers
    item = MediaItem.objects.filter(pk=media_id, published=True).first()
    if item is None or paragraph >= len(item.paragraphs):
        raise AssistanceError('invalid_selection', 'That published passage is unavailable.')
    text = item.paragraphs[paragraph]
    if not (0 <= start < end <= len(text)) or end - start > max_chars or not text[start:end].strip():
        raise AssistanceError('invalid_selection', f'Choose between 1 and {max_chars} characters within one paragraph.')
    locale = data.get('locale', '')
    explanation_locale = data.get('explanation_locale', 'en')
    if not isinstance(locale, str) or not LOCALE.fullmatch(locale) or not isinstance(explanation_locale, str) or not LOCALE.fullmatch(explanation_locale):
        raise AssistanceError('invalid_locale', 'Choose a supported language code.')
    expected = LANGUAGES.get(item.language, item.language.lower())
    if locale.split('-')[0] != expected.split('-')[0]:
        raise AssistanceError('invalid_locale', 'The reference language must match the media language.')
    # Keep selection plus nearby context within a hard total bound, even for long paragraphs.
    context_size = max(800, end - start)
    left = max(0, start - (context_size - (end - start)) // 2)
    left = max(0, min(left, len(text) - context_size))
    return {'selection': text[start:end], 'context': text[left:left + context_size],
            'language': locale, 'explanation_locale': explanation_locale}


def validate_wav(raw):
    if len(raw) > 5 * 1024 * 1024:
        raise AssistanceError('clip_too_large', 'Record at most 60 seconds and 5 MiB.', 413)
    if len(raw) < 44 or raw[:4] != b'RIFF' or raw[8:12] != b'WAVE' or struct.unpack('<I', raw[4:8])[0] + 8 != len(raw):
        raise AssistanceError('invalid_audio', 'Upload a complete mono PCM WAV recording.')
    try:
        with wave.open(io.BytesIO(raw), 'rb') as recording:
            frames, rate = recording.getnframes(), recording.getframerate()
            if (recording.getnchannels() != 1 or recording.getsampwidth() != 2
                    or recording.getcomptype() != 'NONE' or not 8000 <= rate <= 48000
                    or not 0 < frames <= rate * 60):
                raise ValueError
            samples = recording.readframes(frames)
            if len(samples) != frames * 2 or not any(samples):
                raise ValueError
            amplitudes = array('h', samples)
            # Reject digital silence, near-silence and constant DC recordings.
            if max(amplitudes) - min(amplitudes) < 32:
                raise ValueError
    except (wave.Error, EOFError, ValueError, struct.error):
        raise AssistanceError('invalid_audio', 'Use a non-silent mono 16-bit PCM WAV recording of at most 60 seconds.') from None
    return raw


def output_schema(practice=False):
    names = ('transcript', 'reference_match', 'uncertainty') if practice else (
        'meaning', 'translation', 'ipa', 'sound_guidance', 'approximation', 'caveat', 'uncertainty')
    properties = {key: {'type': 'STRING'} for key in names}
    entry_keys = ('observation', 'suggestion') if practice else ('text', 'note')
    properties['feedback' if practice else 'examples'] = {'type': 'ARRAY', 'items': {
        'type': 'OBJECT', 'properties': {key: {'type': 'STRING'} for key in entry_keys}, 'required': list(entry_keys)}}
    if practice:
        properties['assessment_supported'] = {'type': 'BOOLEAN'}
    return {'type': 'OBJECT', 'properties': properties, 'required': list(properties)}


def validate_output(data, practice=False):
    def text(value, limit=1800):
        if not isinstance(value, str) or len(value) > limit:
            raise ValueError
        return value
    try:
        if not isinstance(data, dict):
            raise ValueError
        if practice:
            if type(data.get('assessment_supported')) is not bool:
                raise ValueError
            result = {key: text(data[key]) for key in ('transcript', 'reference_match', 'uncertainty')}
            entries = data['feedback']
            if not isinstance(entries, list) or len(entries) > 6:
                raise ValueError
            result['feedback'] = [{key: text(entry[key], 800) for key in ('observation', 'suggestion')} for entry in entries]
            result['assessment_supported'] = data['assessment_supported']
            if not result['assessment_supported']:
                result['feedback'] = []
            return result
        result = {key: text(data[key]) for key in ('meaning', 'translation', 'ipa', 'sound_guidance', 'approximation', 'caveat', 'uncertainty')}
        entries = data['examples']
        if not isinstance(entries, list) or len(entries) > 5:
            raise ValueError
        result['examples'] = [{key: text(entry[key], 500) for key in ('text', 'note')} for entry in entries]
        return result
    except (ValueError, KeyError, TypeError):
        raise AssistanceError('invalid_provider_output', 'The assistant returned an unusable response. Try again.', 502) from None
