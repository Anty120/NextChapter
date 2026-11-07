from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.db import models
from django.urls import reverse


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
