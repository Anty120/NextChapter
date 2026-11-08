from django.contrib import admin

from .models import Club, Comment, MediaItem, Membership, ReadingProgress, Report
from .models import UploadedMedia
from .upload_forms import ReviewForm
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html


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


@admin.register(UploadedMedia)
class UploadedMediaAdmin(admin.ModelAdmin):
    """Only voluntarily submitted records enter the staff review queue."""
    form = ReviewForm
    actions = None
    list_display = ['title','owner','kind','language','review_status','submitted_at']
    list_filter = ['review_status','kind','language']
    search_fields = ['title','creator','owner__username']
    fields = ['title','owner','creator','language','kind','description','preview',
              'license_name','source_url','rights_note','submitted_at','review_status',
              'review_notes','reviewed_by','reviewed_at']
    readonly_fields = [f for f in fields if f not in ['review_status','review_notes']]

    def get_queryset(self,request):
        query = super().get_queryset(request).exclude(review_status='private').defer('content')
        # ModelAdmin wraps change POSTs in a transaction; lock before validation.
        return query.select_for_update() if request.method == 'POST' else query

    def has_add_permission(self,request):
        return False

    def has_delete_permission(self,request,obj=None):
        return False

    @admin.display(description='Read or listen before deciding')
    def preview(self,obj):
        if obj.review_status == 'pending':
            return format_html('<a href="{}">Open submitted file</a>',reverse('uploads:review_detail',args=[obj.pk]))
        if obj.review_status == 'approved':
            return format_html('<a href="{}">Open public contribution</a>',obj.public_url)
        return 'Request changes or ask the uploader to submit again.'

    def save_model(self,request,obj,form,change):
        if obj.review_status in ['approved','rejected']:
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
        super().save_model(request,obj,form,change)
