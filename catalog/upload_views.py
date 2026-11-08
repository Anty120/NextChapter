"""Personal library and opt-in review. Raw storage never has a public URL."""
import re

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import RequestDataTooBig, TooManyFieldsSent, TooManyFilesSent
from django.core.paginator import Paginator
from django.db import IntegrityError, OperationalError, transaction
from django.db.models import Sum
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import content_disposition_header
from django.utils.text import slugify
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .models import UploadedMedia
from .upload_forms import SubmissionForm, UploadForm, UploadMetadataForm, UploadProgressForm
from .upload_validation import MAX_FILE_BYTES, MAX_USER_BYTES, MAX_USER_FILES
from .upload_limits import DIRECT_UPLOAD_BYTES, CHUNK_BYTES


def owned(request, pk, content=False):
    query = UploadedMedia.objects.filter(owner=request.user)
    if not content:
        query = query.defer('content')
    return get_object_or_404(query, pk=pk)


@never_cache
@login_required
@require_GET
def library(request):
    from .song_uploads import cleanup_expired
    cleanup_expired()
    items = UploadedMedia.objects.filter(owner=request.user).defer('content')
    used = items.aggregate(total=Sum('byte_size'))['total'] or 0
    return render(request, 'catalog/uploads/library.html', {
        'uploads':Paginator(items,12).get_page(request.GET.get('page')),
        'used_bytes':used, 'total_bytes':MAX_USER_BYTES,
    })


@never_cache
@login_required
@require_http_methods(['GET','POST'])
def create(request):
    form, status = UploadForm(), 200
    if request.method == 'POST':
        try:
            length = int(request.META.get('CONTENT_LENGTH') or 0)
        except ValueError:
            length = MAX_FILE_BYTES + 65537
        if length > MAX_FILE_BYTES + 65536:
            form = UploadForm(data={})
            form.add_error(None, 'PDFs may be up to 3 MiB. MP3s may be up to 10 MB; enable JavaScript for larger songs.')
            status = 413
        else:
            try:
                post, files = request.POST, request.FILES
                rejected = getattr(request,'upload_rejected',False)
                form = UploadForm(post, None if rejected else files)
                if rejected:
                    form.add_error(None,'Choose one PDF up to 3 MiB or MP3 up to 10 MB. Larger songs need JavaScript enabled.')
                if len(files) != 1 or len(files.getlist('file')) != 1:
                    form.add_error(None, 'Choose exactly one PDF or MP3 file.')
                if form.is_valid():
                    data = form.inspected
                    # Lock the account so concurrent uploads cannot bypass its quota.
                    with transaction.atomic():
                        get_user_model().objects.select_for_update().get(pk=request.user.pk)
                        entries = UploadedMedia.objects.filter(owner=request.user)
                        existing = entries.defer('content').filter(sha256=data['sha256']).first()
                        if existing:
                            messages.info(request, 'That file is already in your library.')
                            return redirect(existing)
                        from .song_uploads import reservation
                        reserved_bytes,reserved_files=reservation(request.user)
                        used = entries.aggregate(total=Sum('byte_size'))['total'] or 0
                        if entries.count()+reserved_files >= MAX_USER_FILES or used+reserved_bytes+data['byte_size'] > MAX_USER_BYTES:
                            form.add_error(None, 'Your library is full (30 files or 30 MiB). Delete an upload to make room.')
                        else:
                            item = form.save(commit=False)
                            item.owner = request.user
                            for key,value in data.items():
                                setattr(item,key,value)
                            item.permission_confirmed_at = timezone.now()
                            item.save()
                            messages.success(request, 'Uploaded to your private library.')
                            return redirect(item)
                status = 400
            except (RequestDataTooBig, TooManyFieldsSent, TooManyFilesSent):
                form = UploadForm(data={})
                form.add_error(None, 'Choose one PDF up to 3 MiB or MP3 up to 10 MB. Larger songs need JavaScript enabled.')
                status = 413
            except (IntegrityError, OperationalError):
                form = UploadForm(data={})
                form.add_error(None, 'Your library is busy. Please retry the upload in a moment.')
                status = 503
    return render(request, 'catalog/uploads/form.html', {'form':form}, status=status)


@never_cache
@login_required
@require_GET
def detail(request, pk):
    item = owned(request, pk)
    return render(request, 'catalog/uploads/detail.html', {'upload':item, 'personal':True,
        'file_url':item.get_absolute_url()+'file/'})


@never_cache
@login_required
@require_http_methods(['GET','HEAD'])
def file(request, pk):
    item = owned(request,pk,content=request.method != 'HEAD')
    return file_response(request,item)


def file_response(request,item):
    size = item.byte_size
    filename = (slugify(item.title)[:80] or 'upload')+'.'+item.extension
    if size > DIRECT_UPLOAD_BYTES and request.method == 'GET' and not request.headers.get('Range'):
        return render(request, 'catalog/uploads/download.html', {
            'upload':item, 'file_url':request.path, 'filename':filename,
        })
    start, end, status = 0, size-1, 200
    selected = request.headers.get('Range')
    if selected:
        match = re.fullmatch(r'bytes=(\d{0,12})-(\d{0,12})', selected)
        if not match or not any(match.groups()):
            response = HttpResponse(status=416); response['Content-Range'] = f'bytes */{size}'; return response
        left,right = match.groups()
        if left:
            start = int(left); end = min(int(right),size-1) if right else size-1
        else:
            suffix = int(right); start = max(0,size-suffix)
            if not suffix:
                start = size
        if start >= size or start > end:
            response = HttpResponse(status=416); response['Content-Range'] = f'bytes */{size}'; return response
        status = 206
        if size > DIRECT_UPLOAD_BYTES:
            end = min(end, start + CHUNK_BYTES - 1)
    body = b'' if request.method == 'HEAD' else bytes(item.content)[start:end+1]
    response = HttpResponse(body, content_type=item.mime, status=status)
    response['Content-Length'] = str(end-start+1)
    response['Accept-Ranges'] = 'bytes'
    if status == 206:
        response['Content-Range'] = f'bytes {start}-{end}/{size}'
    response['Content-Disposition'] = content_disposition_header(request.GET.get('download')=='1',filename)
    response['X-Content-Type-Options'] = 'nosniff'
    response['X-Frame-Options'] = 'SAMEORIGIN'
    response['Content-Security-Policy'] = "sandbox; default-src 'none'; frame-ancestors 'self'; base-uri 'none'; form-action 'none'"
    response['Referrer-Policy'] = 'no-referrer'
    return response


@never_cache
@login_required
@require_POST
def progress(request,pk):
    item = owned(request,pk)
    form = UploadProgressForm(request.POST)
    if form.is_valid():
        if item.kind == 'book':
            page = form.cleaned_data['page']
            if page is not None and page <= item.page_count:
                item.saved_page = page; item.save(update_fields=['saved_page'])
                if request.headers.get('Accept') == 'application/json':
                    return JsonResponse({'saved':True})
                messages.success(request,'Your page is saved.'); return redirect(item)
        else:
            seconds = form.cleaned_data['seconds']
            if seconds is not None and seconds <= item.duration_seconds:
                item.saved_seconds = seconds; item.save(update_fields=['saved_seconds'])
                if request.headers.get('Accept') == 'application/json':
                    return JsonResponse({'saved':True})
                messages.success(request,'Your listening position is saved.'); return redirect(item)
    return JsonResponse({'error':'Choose a valid page or listening position.'},status=400)


@never_cache
@login_required
@require_http_methods(['GET','POST'])
def delete(request,pk):
    item = owned(request,pk)
    if request.method == 'POST':
        if request.POST.get('confirm') != 'delete':
            return HttpResponse('Confirm deletion.',status=400)
        item.delete()
        messages.success(request,'The upload and its saved position were deleted.')
        return redirect('uploads:library')
    return render(request,'catalog/uploads/delete.html',{'upload':item})


@never_cache
@login_required
@require_http_methods(['GET','POST'])
def submit(request,pk):
    with transaction.atomic():
        item = get_object_or_404(UploadedMedia.objects.select_for_update().defer('content'),pk=pk,owner=request.user)
        if item.review_status in {'pending','approved'}:
            messages.info(request,'This upload is already submitted or published. You can withdraw it from its library page.')
            return redirect(item)
        form = SubmissionForm(request.POST if request.method == 'POST' else None, initial={
            'creator':item.creator, 'rights_note':item.rights_note, 'license_name':item.license_name, 'source_url':item.source_url})
        if request.method == 'POST' and form.is_valid():
            for key in ['creator','rights_note','license_name','source_url']:
                setattr(item,key,form.cleaned_data[key])
            item.review_status='pending';item.submitted_at=timezone.now()
            item.reviewed_at=None;item.reviewed_by=None;item.review_notes=''
            item.save(update_fields=['creator','rights_note','license_name','source_url','review_status',
                                     'submitted_at','reviewed_at','reviewed_by','review_notes'])
            messages.success(request,'Submitted for staff review. Your file stays private until approved.')
            return redirect(item)
    return render(request,'catalog/uploads/submit.html',{'upload':item,'form':form},status=400 if form.errors else 200)


@never_cache
@login_required
@require_POST
def withdraw(request,pk):
    # One update shares the same row lock as staff approval, so a stale review
    # cannot republish a withdrawn contribution.
    changed = UploadedMedia.objects.filter(pk=pk,owner=request.user).update(review_status='private',reviewed_at=None,reviewed_by=None)
    if not changed:
        raise Http404('Upload not found.')
    messages.success(request,'Withdrawn from review and the public shelf. Your private copy remains.')
    return redirect('uploads:detail',pk=pk)


@never_cache
@login_required
@require_http_methods(['GET','POST'])
def edit(request,pk):
    with transaction.atomic():
        item=get_object_or_404(UploadedMedia.objects.select_for_update().defer('content'),pk=pk,owner=request.user)
        form=UploadMetadataForm(request.POST if request.method=='POST' else None,instance=item)
        if request.method=='POST' and form.is_valid():
            if form.has_changed():
                item=form.save(commit=False)
                item.review_status='private';item.reviewed_at=None;item.reviewed_by=None
                item.save(update_fields=['title','creator','language','description','review_status','reviewed_at','reviewed_by'])
                messages.success(request,'Details saved. Your upload is private; submit it again if you want to share the changes.')
            return redirect(item)
    return render(request,'catalog/uploads/edit.html',{'upload':item,'form':form},status=400 if form.errors else 200)


@never_cache
@require_GET
def public_detail(request,pk):
    item=get_object_or_404(UploadedMedia.objects.defer('content'),pk=pk,review_status='approved')
    from django.urls import reverse
    return render(request,'catalog/uploads/detail.html',{'upload':item,'public':True,
        'file_url':reverse('uploads:public_file',args=[pk])})


@never_cache
@require_http_methods(['GET','HEAD'])
def public_file(request,pk):
    item=get_object_or_404(UploadedMedia,pk=pk,review_status='approved')
    return file_response(request,item)


@never_cache
@staff_member_required
@permission_required('catalog.change_uploadedmedia',raise_exception=True)
@require_GET
def review_detail(request,pk):
    item=get_object_or_404(UploadedMedia.objects.defer('content'),pk=pk,review_status='pending')
    from django.urls import reverse
    return render(request,'catalog/uploads/detail.html',{'upload':item,'reviewing':True,
        'file_url':reverse('uploads:review_file',args=[pk])})


@never_cache
@staff_member_required
@permission_required('catalog.change_uploadedmedia',raise_exception=True)
@require_http_methods(['GET','HEAD'])
def review_file(request,pk):
    item=get_object_or_404(UploadedMedia,pk=pk,review_status='pending')
    return file_response(request,item)
