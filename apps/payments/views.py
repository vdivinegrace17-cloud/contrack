from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect

from apps.accounts.decorators import organizer_required, merchant_required
from .models import Payment
from apps.reservations.models import Application


# ── Merchant views ────────────────────────────────────────────────────────────

@merchant_required
def submit_payment(request, application_pk):
    """Merchant submits proof of payment for an APPROVED application."""
    app = get_object_or_404(Application, pk=application_pk, merchant=request.user,
                            status=Application.Status.APPROVED)
    # TODO: PaymentForm — amount_declared, payment_method, reference_number, proof_image
    return render(request, 'payments/submit_payment.html', {'application': app})


@login_required
def payment_detail(request, pk):
    """View a payment submission (merchant or organizer)."""
    payment = get_object_or_404(Payment, pk=pk)
    if request.user.is_merchant and payment.application.merchant != request.user:
        return redirect('merchant:dashboard')
    return render(request, 'payments/payment_detail.html', {'payment': payment})


# ── Organizer views ───────────────────────────────────────────────────────────

@organizer_required
def organizer_payment_list(request):
    """Organizer sees all payments system-wide with optional filtering."""
    payments = Payment.objects.select_related(
        'application__merchant', 'application__event', 'application__booth'
    ).order_by('-submitted_at')
    status = request.GET.get('status', '')
    q      = request.GET.get('q', '')

    if status:
        payments = payments.filter(status=status)
    if q:
        payments = payments.filter(
            Q(application__merchant__username__icontains=q) |
            Q(application__event__title__icontains=q)
        )

    context = {
        'payments':       payments,
        'status':         status,
        'q':              q,
        'status_choices': Payment.Status.choices,
    }
    return render(request, 'organizer/payment_list.html', context)


@organizer_required
def pending_payments(request, event_slug):
    """Organizer sees PENDING payments for a specific event."""
    payments = Payment.objects.filter(
        application__event__slug=event_slug,
        status=Payment.Status.PENDING,
    ).select_related('application__merchant', 'application__booth')
    return render(request, 'payments/pending_payments.html', {'payments': payments})


@organizer_required
def verify_payment(request, pk):
    """Organizer marks a payment as VERIFIED."""
    payment = get_object_or_404(Payment, pk=pk)
    # TODO: set payment.status = VERIFIED, record verified_by/verified_at, create Notification
    return redirect('organizer:pending_payments', event_slug=payment.application.event.slug)


@organizer_required
def reject_payment(request, pk):
    """Organizer rejects a payment with a reason."""
    payment = get_object_or_404(Payment, pk=pk)
    # TODO: RejectPaymentForm with rejection_reason
    return render(request, 'payments/reject_payment.html', {'payment': payment})
