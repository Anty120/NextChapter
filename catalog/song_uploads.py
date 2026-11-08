"""Large songs travel in small authenticated, retry-safe requests."""
import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction, OperationalError, IntegrityError
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .models import SongUploadDraft, UploadedMedia
from .upload_forms import UploadMetadataForm
from .upload_limits import CHUNK_BYTES, DIRECT_UPLOAD_BYTES, MAX_SONG_BYTES, MAX_USER_BYTES, MAX_USER_FILES
from .upload_validation import inspect_file


def cleanup_expired():
    return SongUploadDraft.objects.filter(expires_at__lte=timezone.now()).delete()


def reservation(owner):
    draft=SongUploadDraft.objects.filter(owner=owner,complete=False,expires_at__gt=timezone.now()).only('expected_size').first()
    return (draft.expected_size,1) if draft else (0,0)


def failure(message,status=400,**extra):
    return JsonResponse({'error':message,**extra},status=status)


@never_cache
@login_required
@require_POST
def start(request):
    if request.content_type!='application/json' or len(request.body)>8192:
        return failure('Send valid song details.',400)
    try:data=json.loads(request.body)
    except (ValueError,UnicodeDecodeError):return failure('Send valid song details.')
    if not isinstance(data,dict):return failure('Send valid song details.')
    size=data.get('size')
    if type(size) is not int or not DIRECT_UPLOAD_BYTES<size<=MAX_SONG_BYTES:
        return failure('MP3 songs must be 10 MB (10,000,000 bytes) or less.')
    if data.get('permission') is not True:
        return failure('Confirm that you own this file or have upload permission.')
    form=UploadMetadataForm(data)
    if not form.is_valid():return failure('Check the title, author and language.',fields=form.errors.get_json_data())
    cleanup_expired()
    try:
        with transaction.atomic():
            get_user_model().objects.select_for_update().get(pk=request.user.pk)
            items=UploadedMedia.objects.filter(owner=request.user)
            used=items.aggregate(total=Sum('byte_size'))['total'] or 0
            if items.count()>=MAX_USER_FILES or used+size>MAX_USER_BYTES:
                return failure('Your library is full. Delete an upload to make room.')
            # A fresh user action replaces only that account's unfinished attempt.
            SongUploadDraft.objects.filter(owner=request.user).delete()
            draft=SongUploadDraft.objects.create(owner=request.user,expected_size=size,
                metadata=form.cleaned_data,expires_at=timezone.now()+timedelta(minutes=30))
        return JsonResponse({'id':str(draft.pk),'chunk_bytes':CHUNK_BYTES,
            'chunk_url':reverse('uploads:song_chunk',args=[draft.pk]),
            'finish_url':reverse('uploads:song_finish',args=[draft.pk]),
            'cancel_url':reverse('uploads:song_cancel',args=[draft.pk])})
    except (OperationalError,IntegrityError):return failure('Your library is busy. Please retry.',503)


@never_cache
@login_required
@require_POST
def chunk(request,pk):
    if request.content_type!='application/octet-stream' or not 0<len(request.body)<=CHUNK_BYTES:
        return failure('Send one bounded song chunk.')
    offset=request.GET.get('offset','')
    if not offset.isascii() or not offset.isdigit() or len(offset)>9:
        return failure('Invalid chunk position.')
    offset=int(offset)
    try:
        with transaction.atomic():
            get_user_model().objects.select_for_update().get(pk=request.user.pk)
            draft=get_object_or_404(SongUploadDraft.objects.select_for_update(),pk=pk,owner=request.user,expires_at__gt=timezone.now())
            if draft.complete:return failure('This upload is already complete.',409)
            current=bytes(draft.content)
            if offset<len(current) and current[offset:offset+len(request.body)]==request.body:
                return JsonResponse({'offset':len(current)})
            if offset!=len(current):return failure('Retry from the saved upload position.',409,offset=len(current))
            if offset+len(request.body)>draft.expected_size:return failure('Song exceeds its declared size.',413)
            draft.content=current+request.body;draft.save(update_fields=['content'])
            return JsonResponse({'offset':len(draft.content)})
    except (OperationalError,IntegrityError):return failure('Your library is busy. Please retry.',503)


@never_cache
@login_required
@require_POST
def finish(request,pk):
    try:
        with transaction.atomic():
            get_user_model().objects.select_for_update().get(pk=request.user.pk)
            draft=get_object_or_404(SongUploadDraft.objects.select_for_update(),pk=pk,owner=request.user,expires_at__gt=timezone.now())
            if draft.complete:
                if draft.finished_upload_id:return JsonResponse({'url':draft.finished_upload.get_absolute_url()})
                return failure('The completed upload was deleted.',410)
            raw=bytes(draft.content)
            if len(raw)!=draft.expected_size:return failure('The song has not finished uploading.',409,offset=len(raw))
            try:data=inspect_file(SimpleUploadedFile('song.mp3',raw,content_type='audio/mpeg'))
            except ValidationError as exc:
                draft.delete();return failure(' '.join(exc.messages))
            items=UploadedMedia.objects.filter(owner=request.user)
            item=items.defer('content').filter(sha256=data['sha256']).first()
            if item is None:
                used=items.aggregate(total=Sum('byte_size'))['total'] or 0
                if items.count()>=MAX_USER_FILES or used+len(raw)>MAX_USER_BYTES:
                    draft.delete();return failure('Your library is full. Delete an upload to make room.')
                item=UploadedMedia.objects.create(owner=request.user,**draft.metadata,**data,permission_confirmed_at=timezone.now())
            draft.complete=True;draft.finished_upload=item;draft.content=b''
            draft.save(update_fields=['complete','finished_upload','content'])
            return JsonResponse({'url':item.get_absolute_url()})
    except (OperationalError,IntegrityError):return failure('Your library is busy. Please retry.',503)


@never_cache
@login_required
@require_POST
def cancel(request,pk):
    draft=get_object_or_404(SongUploadDraft,pk=pk,owner=request.user)
    draft.delete();return JsonResponse({'cancelled':True})
