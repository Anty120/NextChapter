"""Presentation-only helpers for the catalog templates."""
from django import template

register = template.Library()

# A cover keeps one colour wherever it appears (shelf card, detail page, club
# card), so the cross-page view transition morphs one object instead of
# cross-fading two differently coloured ones. The old shelf cycled colours by
# list position, which recoloured a book whenever a filter changed.
COVER_COLORS = ('orange', 'purple', 'green', 'yellow', 'pink', 'cream', 'blue')
CLUB_COLORS = ('blue', 'purple', 'green', 'yellow')
# Small resting tilts, like prints laid on a table. Kept under 1.5deg so text
# stays easy to read; hover straightens the card.
POSES = ('-1.2deg', '0.8deg', '-0.5deg', '1.1deg', '-0.9deg', '0.4deg', '-0.3deg')


@register.filter
def cover_color(obj):
    return COVER_COLORS[(obj.pk or 0) % len(COVER_COLORS)]


@register.filter
def club_color(obj):
    return CLUB_COLORS[(obj.pk or 0) % len(CLUB_COLORS)]


@register.filter
def pose(index):
    try:
        return POSES[int(index) % len(POSES)]
    except (TypeError, ValueError):
        return '0deg'
