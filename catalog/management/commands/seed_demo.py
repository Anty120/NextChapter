from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.demo_content import BAKERY, ENGLISH_AUDIO, FRENCH, GARDEN, LETTER, MARKET, TRAIN
from catalog.models import Club, MediaItem


class Command(BaseCommand):
    help = 'Create/update the original demo catalog and club. Safe to run repeatedly; never resets user activity or passwords.'

    @transaction.atomic
    def handle(self, *args, **options):
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
        audio, _ = MediaItem.objects.update_or_create(slug='the-blue-door', defaults={
            'title': 'The Blue Door', 'creator': 'NextChapter Studio', 'language': 'English',
            'format': MediaItem.Format.AUDIOBOOK, 'level': 'A1', 'text': ENGLISH_AUDIO,
            'description': 'Listen to a gentle morning at the neighborhood bakery. Transcript included.',
            'audio_file': 'catalog/audio/the-blue-door.wav', 'published': True,
            'attribution': attribution + ' Bundled synthetic narration rendered with Microsoft Zira (en-US). This is a demo voice, not a human contributor.',
            'cultural_context': 'An original English adaptation of our fictional bakery scene. No claim to represent a specific region or accent community.',
            'difficulty_note': 'Approximate A1 editorial estimate: slow synthetic narration and short everyday sentences. Reading and listening comfort may differ.',
        })
        audio.full_clean()
        Club.objects.update_or_create(slug='the-morning-pages', defaults={
            'name': 'The Morning Pages', 'language': 'Spanish',
            'description': 'A welcoming corner for short stories, everyday culture, and good conversation. All levels welcome. Start with the bakery story and share a memory of a place that feels like home.',
            'featured_media': MediaItem.objects.get(slug='la-panaderia'),
        })
        self.stdout.write(self.style.SUCCESS('Demo ready: 7 media items and The Morning Pages club. Existing memberships, comments, reports, and progress preserved.'))
