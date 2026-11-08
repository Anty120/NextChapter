from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from .forms import CommentForm, ProgressForm, ReportForm
from .models import Club, Comment, MediaItem, Membership, ReadingProgress
from .quizzes import book_quiz, public_questions


@require_GET
def catalog(request):
    items = MediaItem.objects.filter(published=True)
    filters = {key: request.GET.get(key, '').strip() for key in ('language', 'format', 'level', 'q')}
    for field in ('language', 'format', 'level'):
        if filters[field]:
            items = items.filter(**{field: filters[field]})
    if filters['q']:
        items = items.filter(Q(title__icontains=filters['q']) | Q(creator__icontains=filters['q']))
    recent = None
    if request.user.is_authenticated:
        recent = ReadingProgress.objects.filter(user=request.user, media__published=True).select_related('media').first()
    return render(request, 'catalog/catalog.html', {
        'items': items, 'filters': filters, 'formats': MediaItem.Format.choices,
        'levels': MediaItem.LEVELS,
        'languages': MediaItem.objects.filter(published=True).values_list('language', flat=True).distinct().order_by('language'),
        'recent': recent,
    })


@require_GET
def media_detail(request, pk):
    item = get_object_or_404(MediaItem, pk=pk, published=True)
    progress = None
    if request.user.is_authenticated:
        progress = ReadingProgress.objects.filter(user=request.user, media=item).first()
    # The manifest helper is owned by the seed worker; custom items return {}.
    from .library import get_media_metadata

    metadata = get_media_metadata(item.slug)
    paragraphs = item.paragraphs
    chapters = [chapter for chapter in metadata.get('chapters', [])
                if isinstance(chapter.get('start_paragraph'), int)
                and 0 <= chapter['start_paragraph'] < len(paragraphs)]
    mime = metadata.get('audio_mime') or {
        '.mp3': 'audio/mpeg', '.ogg': 'audio/ogg', '.wav': 'audio/wav',
    }.get(item.audio_file.lower()[-4:], '')
    duration = metadata.get('duration_seconds')
    duration_label = ''
    if isinstance(duration, (int, float)) and duration > 0:
        minutes, seconds = divmod(round(duration), 60)
        duration_label = f'{minutes}:{seconds:02d}'
    return render(request, 'catalog/media_detail.html', {
        'item': item, 'progress': progress, 'report_form': ReportForm(),
        'metadata': metadata, 'chapters': chapters, 'paragraphs': paragraphs,
        'audio_mime': mime, 'duration_label': duration_label,
        'has_quiz': item.format == 'book' and bool(book_quiz(item.slug)),
        'clubs': Club.objects.filter(featured_media=item),
    })


@require_http_methods(['GET', 'POST'])
def book_quiz_view(request, pk):
    item = get_object_or_404(MediaItem, pk=pk, published=True, format='book')
    questions = book_quiz(item.slug)
    if not questions:
        from django.http import Http404
        raise Http404('No quiz is available for this book.')
    submitted = request.POST if request.method == 'POST' else None
    error = ''
    if submitted is not None and any(
            submitted.get(f'q{i}') not in {str(n) for n in range(len(q['choices']))}
            for i, q in enumerate(questions)):
        error = 'Choose one answer for every question, then check your answers.'
    rows = public_questions(questions, submitted if not error else None)
    return render(request, 'catalog/quiz.html', {
        'item': item, 'questions': rows, 'error': error,
        'graded': submitted is not None and not error,
        'score': sum(row.get('correct', False) for row in rows),
    }, status=400 if error else 200)


@require_POST
@login_required
def save_progress(request, pk):
    item = get_object_or_404(MediaItem, pk=pk, published=True)
    form = ProgressForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'error': 'Invalid position.'}, status=400)
    if item.is_audio:
        seconds = form.cleaned_data['seconds']
        if seconds is None:
            return HttpResponseBadRequest('An audio timestamp is required.')
        defaults = {'seconds': seconds}
    else:
        paragraph = form.cleaned_data['paragraph']
        if paragraph is None or paragraph >= len(item.paragraphs):
            return HttpResponseBadRequest('Choose an existing paragraph.')
        defaults = {'paragraph': paragraph}
    ReadingProgress.objects.update_or_create(user=request.user, media=item, defaults=defaults)
    if request.headers.get('Accept') == 'application/json':
        return JsonResponse({'saved': True})
    messages.success(request, 'Your place is saved.')
    response = redirect(item)
    if not item.is_audio:
        response['Location'] += f'#paragraph-{defaults["paragraph"]}'
    return response


@require_GET
def club_list(request):
    return render(request, 'catalog/clubs.html', {'clubs': Club.objects.all().order_by('name')})


def club_context(request, club, form=None):
    member = request.user.is_authenticated and Membership.objects.filter(user=request.user, club=club).exists()
    return {
        'club': club, 'member': member, 'comment_form': form if form is not None else CommentForm(),
        'comments': Paginator(club.comments.select_related('user').order_by('-created_at', '-id'), 20).get_page(request.GET.get('page')),
        'member_count': club.members.count(),
    }


@require_GET
def club_detail(request, pk):
    club = get_object_or_404(Club.objects.select_related('featured_media'), pk=pk)
    return render(request, 'catalog/club_detail.html', club_context(request, club))


@require_POST
@login_required
def club_membership(request, pk):
    club = get_object_or_404(Club, pk=pk)
    action = request.POST.get('action')
    if action == 'join':
        Membership.objects.get_or_create(user=request.user, club=club)
        messages.success(request, 'You joined the club. Welcome!')
    elif action == 'leave':
        Membership.objects.filter(user=request.user, club=club).delete()
        messages.info(request, 'You left the club. Your existing comments remain in the discussion.')
    else:
        return HttpResponseBadRequest('Choose join or leave.')
    return redirect(club)


@require_POST
@login_required
def add_comment(request, pk):
    club = get_object_or_404(Club, pk=pk)
    if not Membership.objects.filter(user=request.user, club=club).exists():
        return HttpResponseForbidden('Join this club before commenting.')
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.user = request.user
        comment.club = club
        comment.save()
        messages.success(request, 'Your comment has been posted.')
        return redirect(club)
    return render(request, 'catalog/club_detail.html', club_context(request, club, form), status=400)


@require_http_methods(['GET', 'POST'])
@login_required
def report(request, kind, pk):
    if kind == 'media':
        target = get_object_or_404(MediaItem, pk=pk, published=True)
        destination = target.get_absolute_url()
    elif kind == 'comment':
        target = get_object_or_404(Comment.objects.select_related('club'), pk=pk)
        destination = target.club.get_absolute_url()
    else:
        return HttpResponseBadRequest('Unknown report target.')
    form = ReportForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        record = form.save(commit=False)
        record.reporter = request.user
        setattr(record, kind, target)
        record.save()
        messages.success(request, 'Report received. A moderator can review it.')
        return redirect(destination)
    return render(request, 'catalog/report.html', {'form': form, 'target': target, 'destination': destination}, status=400 if request.method == 'POST' else 200)


@require_http_methods(['GET', 'POST'])
def signup(request):
    form = UserCreationForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Account created. Sign in to save your place and join a club.')
        return redirect('login')
    return render(request, 'registration/signup.html', {'form': form})
