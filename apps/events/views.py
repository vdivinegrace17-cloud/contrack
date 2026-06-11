from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify

from apps.accounts.decorators import organizer_required
from .models import Event
from .forms import EventForm


def event_list(request):
    """Public event directory — shows all OPEN events."""
    events = Event.objects.filter(status=Event.Status.OPEN).order_by('-start_date')
    return render(request, 'events/event_list.html', {'events': events})


def event_detail(request, slug):
    """Public event detail page with venue map and floor plan link."""
    event = get_object_or_404(Event, slug=slug)
    return render(request, 'events/event_detail.html', {'event': event})


# ── Organizer event management ────────────────────────────────────────────────

@organizer_required
def organizer_event_list(request):
    """Organizer sees all events system-wide with optional filtering."""
    events  = Event.objects.order_by('-created_at')
    status  = request.GET.get('status', '')
    q       = request.GET.get('q', '')

    if status:
        events = events.filter(status=status)
    if q:
        events = events.filter(Q(title__icontains=q) | Q(venue_name__icontains=q))

    context = {
        'events':         events,
        'status':         status,
        'q':              q,
        'status_choices': Event.Status.choices,
    }
    return render(request, 'organizer/event_list.html', context)


@organizer_required
def create_event(request):
    """Organizer creates a new event."""
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.save()
            messages.success(request, f'Event "{event.title}" created successfully.')
            return redirect('organizer:event_list')
    else:
        form = EventForm()
    return render(request, 'organizer/event_form.html', {'form': form, 'action': 'Create'})


@organizer_required
def edit_event(request, slug):
    """Organizer edits an existing event."""
    event = get_object_or_404(Event, slug=slug)
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, f'Event "{event.title}" updated.')
            return redirect('organizer:event_list')
    else:
        form = EventForm(instance=event)
    return render(request, 'organizer/event_form.html', {'form': form, 'event': event, 'action': 'Edit'})


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
