from django.contrib import messages
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.decorators import organizer_required
from .models import Event
from .forms import EventForm


def event_list(request):
    """Public / merchant event directory — shows OPEN and ONGOING events."""
    events = (Event.objects
              .filter(status__in=[Event.Status.OPEN, Event.Status.ONGOING])
              .order_by('-start_date'))
    return render(request, 'events/event_list.html', {'events': events})


def event_detail(request, slug):
    """Public event detail page."""
    event = get_object_or_404(Event, slug=slug)
    return render(request, 'events/event_detail.html', {'event': event})


# ── Organizer event management ────────────────────────────────────────────────

@organizer_required
def organizer_event_list(request):
    """Organizer sees all events with booth counts."""
    from apps.booths.models import Booth
    events = (Event.objects
              .annotate(
                  total_booths=Count('booths', filter=Q(booths__is_landmark=False)),
                  available_booths=Count('booths', filter=Q(booths__is_landmark=False, booths__status=Booth.Status.AVAILABLE)),
                  reserved_booths=Count('booths', filter=Q(booths__is_landmark=False, booths__status=Booth.Status.RESERVED)),
              )
              .order_by('-created_at'))
    status = request.GET.get('status', '')
    q      = request.GET.get('q', '')

    if status:
        events = events.filter(status=status)
    if q:
        events = events.filter(Q(title__icontains=q) | Q(venue_name__icontains=q))

    context = {
        'events':             events,
        'status':             status,
        'q':                  q,
        'status_choices':     Event.Status.choices,
        'event_type_choices': Event.EventType.choices,
    }
    return render(request, 'organizer/event_list.html', context)


@organizer_required
@require_POST
def publish_event(request, slug):
    event = get_object_or_404(Event, slug=slug, status=Event.Status.DRAFT)
    event.status = Event.Status.OPEN
    event.save(update_fields=['status'])
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    messages.success(request, f'"{event.title}" published.')
    return redirect('organizer:event_list')


@organizer_required
def create_event(request):
    """Organizer creates a new event. Supports AJAX (returns JSON) or normal POST (redirect)."""
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.save()
            if is_ajax:
                return JsonResponse({'success': True})
            messages.success(request, f'Event "{event.title}" created successfully.')
            return redirect('organizer:event_list')
        else:
            if is_ajax:
                return JsonResponse({'success': False, 'errors': form.errors})
            return render(request, 'organizer/event_list.html', {'form': form})
    return redirect('organizer:event_list')


@organizer_required
def edit_event(request, slug):
    """Organizer edits an existing event. Supports AJAX (returns JSON) or normal POST (redirect)."""
    event = get_object_or_404(Event, slug=slug)
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if form.is_valid():
            form.save()
            if is_ajax:
                return JsonResponse({'success': True})
            messages.success(request, f'Event "{event.title}" updated.')
            return redirect('organizer:event_list')
        else:
            if is_ajax:
                return JsonResponse({'success': False, 'errors': form.errors})
    return redirect('organizer:event_list')


@organizer_required
def event_data(request, slug):
    """Returns event fields as JSON for pre-filling the edit modal."""
    event = get_object_or_404(Event, slug=slug)
    fmt = '%Y-%m-%dT%H:%M'
    return JsonResponse({
        'title':                  event.title,
        'description':            event.description,
        'event_type':             event.event_type,
        'start_date':             event.start_date.strftime(fmt) if event.start_date else '',
        'end_date':               event.end_date.strftime(fmt) if event.end_date else '',
        'application_open_date':  event.application_open_date.strftime(fmt) if event.application_open_date else '',
        'application_close_date': event.application_close_date.strftime(fmt) if event.application_close_date else '',
        'venue_name':             event.venue_name,
        'address':                event.address,
        'status':                 event.status,
    })


@organizer_required
def delete_event(request, slug):
    """Organizer deletes a DRAFT event."""
    event = get_object_or_404(Event, slug=slug)
    if request.method == 'POST':
        title = event.title
        event.delete()
        messages.success(request, f'Event "{title}" deleted.')
        return redirect('organizer:event_list')
    return render(request, 'organizer/event_confirm_delete.html', {'event': event})
