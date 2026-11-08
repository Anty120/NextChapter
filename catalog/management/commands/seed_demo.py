from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalog.demo_content import BAKERY, FRENCH, GARDEN, LETTER, MARKET, TRAIN
from catalog.models import Club, MediaItem
from catalog.library import LibraryError, load_demo_library


class Command(BaseCommand):
    help = 'Validate the complete bundled library, then update demo rows without resetting user activity.'

    def handle(self, *args, **options):
        try:
            media, clubs, _ = load_demo_library()
        except (LibraryError, OSError) as exc:
            raise CommandError(str(exc)) from exc
        with transaction.atomic():
            self.seed(media, clubs)
        self.stdout.write(self.style.SUCCESS(
            f'Demo ready: {len(media)} manifest media, 6 original stories, '
            f"{len(set(clubs) | {'the-morning-pages'})} demo clubs. Existing IDs and user activity preserved."))

    def seed(self, media, clubs):
        stories = [
            ('la-panaderia', 'La panadería de la calle Sol', 'Spanish', 'A1', BAKERY, 'Warm bread, a blue door, and a morning shared with family.', 'A fictional neighborhood bakery. Bread and daily markets connect many communities; this story does not depict a specific country.'),
            ('el-mercado', 'Un día en el mercado', 'Spanish', 'A1', MARKET, 'A red shopping bag leads Elena to an unexpected story.', 'A fictional European neighborhood market. The euro reference places this particular scene in Spain, rather than representing all Spanish-speaking communities.'),
            ('el-huerto', 'Mi abuela y su huerto', 'Spanish', 'A1', GARDEN, 'A small garden becomes a place to share family memories.', 'A fictional family garden. Growing and sharing food can carry personal family histories; this scene is not a claim about a whole culture.'),
            ('el-tren', 'El tren de las ocho', 'Spanish', 'A2', TRAIN, 'A different platform brings an unexpected friendship.', 'A fictional train journey about exchanging personal musical memories, without attributing a single musical tradition to a country.'),
            ('la-carta', 'La carta perdida', 'Spanish', 'A2', LETTER, 'A letter hidden in a used book reveals a neighborhood story.', 'A fictional neighborhood archive and community reading tradition. Named places and historical events are intentionally not asserted.'),
            ('le-livre-jaune', 'Le livre jaune', 'French', 'A1', FRENCH, 'A yellow book brings two friends together.', 'A fictional French-language bookshop and park, without a specified country.'),
        ]
        attribution = 'Original AI-assisted NextChapter demo writing, created for this project. Distributed under the repository MIT license; no third-party text or covers.'
        for slug, title, language, level, text, description, context in stories:
            item, _ = MediaItem.objects.update_or_create(slug=slug, defaults={
                'title': title, 'creator': 'NextChapter Studio', 'language': language,
                'format': MediaItem.Format.STORY, 'level': level, 'text': text,
                'description': description, 'cultural_context': context, 'attribution': attribution,
                'difficulty_note': 'Approximate editorial estimate: short paragraphs and everyday vocabulary. Not certified or a measure of your proficiency.',
                'published': True, 'audio_file': '',
            })
            item.full_clean()
        # Retire unsupported narration without changing its identity or progress.
        MediaItem.objects.filter(slug__in=[
            'the-blue-door', 'audiobook-en-01', 'song-en-01', 'song-en-02',
        ]).update(published=False)
        for slug, defaults in media.items():
            MediaItem.objects.update_or_create(slug=slug, defaults=defaults)
        for slug, club in clubs.items():
            Club.objects.update_or_create(slug=slug, defaults={
                key: club[key] for key in ('name', 'language', 'description')
            } | {'featured_media': MediaItem.objects.get(slug=club['featured_media_slug'])})
        if 'the-morning-pages' not in clubs:
            Club.objects.update_or_create(slug='the-morning-pages', defaults={
                'name': 'The Morning Pages', 'language': 'Spanish',
                'description': 'A welcoming corner for short stories, everyday culture, and good conversation. All levels welcome. Start with the bakery story and share a memory of a place that feels like home.',
                'featured_media': MediaItem.objects.get(slug='la-panaderia'),
            })
