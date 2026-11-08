from django.core.management.base import BaseCommand
from catalog.song_uploads import cleanup_expired


class Command(BaseCommand):
    help = 'Delete expired temporary song upload drafts (also cleaned on library visits/uploads).'

    def handle(self, *args, **options):
        count, _ = cleanup_expired()
        self.stdout.write(f'Removed {count} expired upload drafts.')
