from django.conf import settings


def assistance(request):
    """Only public feature flags reach HTML. Never expose provider configuration."""
    return {
        'assistance_enabled': settings.GEMINI_ENABLED,
        'assistance_voice_enabled': (
            settings.GEMINI_ENABLED
            and settings.GEMINI_VOICE_INPUT_ENABLED
            and settings.GEMINI_VOICE_INPUT_APPROVED
        ),
    }
