from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.db import models
from django.urls import reverse
import uuid


class MediaItem(models.Model):
    class Format(models.TextChoices):
        STORY = 'story', 'Short story'
        BOOK = 'book', 'Book'
        AUDIOBOOK = 'audiobook', 'Audiobook'
        SONG = 'song', 'Song'

    LEVELS = [(level, level) for level in ('A1', 'A2', 'B1', 'B2', 'C1', 'C2')]
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=180)
    creator = models.CharField(max_length=180)
    language = models.CharField(max_length=40)
    format = models.CharField(max_length=12, choices=Format.choices)
    level = models.CharField(max_length=2, choices=LEVELS)
    description = models.TextField(max_length=1000)
    text = models.TextField(blank=True, help_text='Story text or authorized audio transcript. Separate paragraphs with blank lines.')
    audio_file = models.CharField(max_length=240, blank=True, help_text='Bundled static path, e.g. catalog/audio/story.wav')
    attribution = models.TextField()
    cultural_context = models.TextField()
    difficulty_note = models.TextField(default='Editorial estimate, not an official proficiency rating.')
    published = models.BooleanField(default=False)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('media_detail', args=[self.pk])

    @property
    def is_audio(self):
        return self.format in (self.Format.AUDIOBOOK, self.Format.SONG)

    @property
    def paragraphs(self):
        return [p.strip() for p in self.text.split('\n\n') if p.strip()]

    def clean(self):
        super().clean()
        if self.published and self.is_audio and not self.audio_file:
            raise ValidationError({'audio_file': 'Published audio needs a playable static asset.'})
        if self.published and not self.is_audio and not self.text.strip():
            raise ValidationError({'text': 'Published reading items need text.'})
        if self.audio_file and (not self.audio_file.startswith('catalog/audio/') or '..' in self.audio_file or '\\' in self.audio_file):
            raise ValidationError({'audio_file': 'Use a bundled path within catalog/audio/.'})


class Club(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=160)
    description = models.TextField()
    language = models.CharField(max_length=40)
    featured_media = models.ForeignKey(MediaItem, null=True, blank=True, on_delete=models.SET_NULL)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, through='Membership', related_name='clubs')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('club_detail', args=[self.pk])


class Membership(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    club = models.ForeignKey(Club, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'club'], name='unique_club_membership')]

    def __str__(self):
        return f'{self.user} / {self.club}'


class Comment(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.TextField(max_length=2000)
    spoiler = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'id']

    def __str__(self):
        return f'{self.user}: {self.body[:60]}'


class ReadingProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    media = models.ForeignKey(MediaItem, on_delete=models.CASCADE)
    paragraph = models.PositiveIntegerField(default=0)
    seconds = models.FloatField(default=0, validators=[MaxValueValidator(86400)])
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'media'], name='unique_user_media_progress')]
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.user} / {self.media}'


class Report(models.Model):
    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        REVIEWED = 'reviewed', 'Reviewed'
        RESOLVED = 'resolved', 'Resolved'

    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    media = models.ForeignKey(MediaItem, null=True, blank=True, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, null=True, blank=True, on_delete=models.CASCADE)
    reason = models.TextField(max_length=2000)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)
    review_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [models.CheckConstraint(
            condition=(models.Q(media__isnull=False, comment__isnull=True) | models.Q(media__isnull=True, comment__isnull=False)),
            name='report_exactly_one_target',
        )]

    def __str__(self):
        return f'{self.get_status_display()}: {self.reason[:60]}'


class UploadedMedia(models.Model):
    """Private, bounded personal files. Never added to the public seed catalog."""
    class Kind(models.TextChoices):
        BOOK = 'book', 'PDF book'
        SONG = 'song', 'MP3 song'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='uploads')
    title = models.CharField(max_length=180)
    creator = models.CharField(max_length=180, blank=True)
    language = models.CharField(max_length=40)
    kind = models.CharField(max_length=4, choices=Kind.choices)
    description = models.TextField(max_length=1000, blank=True)
    content = models.BinaryField(editable=False)
    byte_size = models.PositiveIntegerField()
    sha256 = models.CharField(max_length=64, editable=False)
    page_count = models.PositiveIntegerField(default=0)
    duration_seconds = models.FloatField(default=0)
    saved_page = models.PositiveIntegerField(default=1)
    saved_seconds = models.FloatField(default=0)
    permission_confirmed_at = models.DateTimeField()
    class ReviewStatus(models.TextChoices):
        PRIVATE = 'private', 'Private'
        PENDING = 'pending', 'Awaiting review'
        APPROVED = 'approved', 'Published'
        REJECTED = 'rejected', 'Changes requested'

    review_status = models.CharField(max_length=8, choices=ReviewStatus.choices, default=ReviewStatus.PRIVATE)
    rights_note = models.TextField(max_length=1500, blank=True)
    license_name = models.CharField(max_length=80, blank=True)
    source_url = models.URLField(max_length=500, blank=True)
    review_notes = models.TextField(max_length=1500, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name='reviewed_uploads')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']
        constraints = [
            models.UniqueConstraint(fields=['owner', 'sha256'], name='unique_owner_uploaded_file'),
            models.CheckConstraint(condition=models.Q(byte_size__gt=0, byte_size__lte=3145728), name='upload_bounded_bytes'),
            models.CheckConstraint(condition=models.Q(kind__in=['book', 'song']), name='upload_supported_kind'),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('uploads:detail', args=[self.pk])

    @property
    def mime(self):
        return 'application/pdf' if self.kind == self.Kind.BOOK else 'audio/mpeg'

    @property
    def extension(self):
        return 'pdf' if self.kind == self.Kind.BOOK else 'mp3'

    @property
    def public_url(self):
        return reverse('uploads:public_detail', args=[self.pk])
