from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect

from apps.accounts.decorators import organizer_required, merchant_required
from .models import Application
from apps.booths.models import Booth
from apps.events.models import Event


# ── Merchant views ────────────────────────────────────────────────────────────

@merchant_required
def apply_for_booth(request, booth_id):
    """Merchant submits a reservation application for a specific booth."""
    booth = get_object_or_404(Booth, pk=booth_id, status=Booth.Status.AVAILABLE)
    # TODO: ApplicationForm — business_name, product_description, special_requests
    #       On save: set booth.status = PENDING
    return render(request, 'reservations/apply.html', {'booth': booth})


@merchant_required
def my_applications(request):
    """Merchant views all their own applications."""
    apps = Application.objects.filter(merchant=request.user).select_related('booth', 'event')
    return render(request, 'merchant/reservation_list.html', {'applications': apps})


@login_required
def application_detail(request, pk):
    """View a single application (merchant owns it or organizer)."""
    app = get_object_or_404(Application, pk=pk)
    if request.user.is_merchant and app.merchant != request.user:
        return redirect('merchant:reservations')
    return render(request, 'reservations/application_detail.html', {'application': app})


@merchant_required
def cancel_application(request, pk):
    """Merchant cancels their own PENDING application."""
    app = get_object_or_404(Application, pk=pk, merchant=request.user, status=Application.Status.PENDING)
    # TODO: set app.status = CANCELLED, set booth.status back to AVAILABLE
    return redirect('merchant:reservations')


# ── Organizer views ───────────────────────────────────────────────────────────

@organizer_required
def organizer_reservation_list(request):
    """Organizer sees all reservations system-wide with optional filtering."""
    apps   = Application.objects.select_related('merchant', 'event', 'booth').order_by('-applied_at')
    status = request.GET.get('status', '')
    q      = request.GET.get('q', '')
    event  = request.GET.get('event', '')

    if status:
        apps = apps.filter(status=status)
    if q:
        apps = apps.filter(
            Q(merchant__username__icontains=q) | Q(event__title__icontains=q)
        )
    if event:
        apps = apps.filter(event__slug=event)

    context = {
        'applications':    apps,
        'status':          status,
        'q':               q,
        'status_choices':  Application.Status.choices,
    }
    return render(request, 'organizer/reservation_list.html', context)


@organizer_required
def event_applications(request, event_slug):
    """Organizer sees all applications for a specific event."""
    event = get_object_or_404(Event, slug=event_slug)
    apps  = Application.objects.filter(event=event).select_related('merchant', 'booth')
    return render(request, 'reservations/event_applications.html', {
        'event': event, 'applications': apps
    })


@organizer_required
def approve_application(request, pk):
    """Organizer approves an application."""
    app = get_object_or_404(Application, pk=pk)
    # TODO: set app.status = APPROVED, booth.status = RESERVED, create Notification
    return redirect('organizer:event_applications', event_slug=app.event.slug)


@organizer_required
def reject_application(request, pk):
    """Organizer rejects an application."""
    app = get_object_or_404(Application, pk=pk)
    # TODO: RejectionForm, set booth back to AVAILABLE, create Notification
    return render(request, 'reservations/reject.html', {'application': app})


@organizer_required
def waitlist_application(request, pk):
    """Organizer moves an application to the waitlist."""
    app = get_object_or_404(Application, pk=pk)
    # TODO: set app.status = WAITLISTED
    return redirect('organizer:event_applications', event_slug=app.event.slug)
