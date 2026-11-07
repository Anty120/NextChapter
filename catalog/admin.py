from django.contrib import admin

from .models import Club, Comment, MediaItem, Membership, ReadingProgress, Report


@admin.register(MediaItem)
class MediaItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'language', 'format', 'level', 'published')
    list_filter = ('published', 'language', 'format', 'level')
    search_fields = ('title', 'creator')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'reporter', 'media', 'comment', 'status', 'created_at')
    list_filter = ('status',)
    readonly_fields = ('reporter', 'media', 'comment', 'reason', 'created_at')
    search_fields = ('reason', 'reporter__username')


admin.site.register([Club, Membership, Comment, ReadingProgress])
