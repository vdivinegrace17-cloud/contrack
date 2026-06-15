import re
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.decorators import organizer_required, merchant_required
from apps.notifications.utils import create_notification
from .models import Application
from apps.booths.models import Booth
from apps.events.models import Event
from apps.payments.models import PaymentSettings

PH_PHONE_RE = re.compile(r'^09\d{9}$')

# ── Merchant views ────────────────────────────────────────────────────────────

@merchant_required
def apply_for_booth(request, booth_id):
    booth = get_object_or_404(Booth, pk=booth_id)

    if request.method == 'GET':
        return JsonResponse({
            'id':       booth.id,
            'label':    booth.display_name,
            'price':    str(booth.price),
            'category': booth.get_category_display(),
            'event':    booth.event.title,
        })

    # POST — accepts multipart/form-data
    if booth.status != Booth.Status.AVAILABLE:
        return JsonResponse({'success': False, 'error': 'This booth is no longer available.'})

    if Application.objects.filter(
        merchant=request.user, booth=booth,
        status__in=[Application.Status.PENDING, Application.Status.APPROVED],
    ).exists():
        return JsonResponse({'success': False, 'error': 'You already have an active application for this booth.'})

    phone = request.POST.get('merchant_phone', '').strip()
    if phone and not PH_PHONE_RE.match(phone):
        return JsonResponse({'success': False, 'error': 'Please enter a valid Philippine mobile number (e.g., 09171234567)'})

    payment_option = request.POST.get('payment_option', 'full')
    price          = booth.price

    if payment_option == 'half':
        first_amt  = price / 2
        second_amt = price / 2
        ps         = PaymentSettings.objects.filter(organizer=booth.event.organizer).first()
        days       = (ps.second_payment_deadline_days if ps and ps.second_payment_deadline_days else 14)
        deadline   = booth.event.start_date.date() - timedelta(days=days)
    else:
        first_amt, second_amt, deadline = price, None, None

    app = Application.objects.create(
        merchant            = request.user,
        booth               = booth,
        event               = booth.event,
        status              = Application.Status.PENDING,
        business_name       = request.POST.get('business_name', '').strip(),
        product_description = request.POST.get('product_description', '').strip(),
        special_requests    = request.POST.get('special_requests', '').strip(),
        payment_option_chosen   = payment_option,
        payment_status          = Application.PaymentStatus.UNPAID,
        first_payment_amount    = first_amt,
        second_payment_amount   = second_amt,
        second_payment_deadline = deadline,
        receipt_image_1         = request.FILES.get('receipt_image_1') or None,
        merchant_name    = request.POST.get('merchant_name', '').strip(),
        merchant_phone   = phone,
        merchant_email   = request.POST.get('merchant_email', '').strip(),
        merchant_facebook= request.POST.get('merchant_facebook', '').strip(),
    )

    booth.status = Booth.Status.PENDING
    booth.save(update_fields=['status'])

    if booth.event.organizer:
        create_notification(
            recipient   = booth.event.organizer,
            notif_type  = 'APP_UPDATE',
            title       = 'New Reservation Submitted',
            message     = (
                f'{app.merchant_name or request.user.username} submitted a reservation '
                f'for {booth.display_name} at {booth.event.title}.'
            ),
            application = app,
        )

    return JsonResponse({'success': True})


@merchant_required
def my_applications(request):
    apps = (Application.objects
            .filter(merchant=request.user, is_disabled=False)
            .select_related('booth', 'event')
            .order_by('-applied_at'))
    status_filter = request.GET.get('status', '')
    if status_filter:
        apps = apps.filter(status=status_filter)
    paginator = Paginator(apps, 10)
    page_obj  = paginator.get_page(request.GET.get('page'))
    return render(request, 'merchant/reservation_list.html', {
        'page_obj':       page_obj,
        'status_filter':  status_filter,
        'status_choices': Application.Status.choices,
    })


@login_required
def application_detail(request, pk):
    app = get_object_or_404(Application, pk=pk)
    if request.user.is_merchant and app.merchant != request.user:
        return redirect('merchant:reservations')

    ps = None
    days_left = None
    if request.user.is_merchant and app.event.organizer:
        ps = PaymentSettings.objects.filter(organizer=app.event.organizer).first()
    if app.second_payment_deadline:
        days_left = app.days_until_second_deadline

    return render(request, 'reservations/application_detail.html', {
        'application': app,
        'ps':          ps,
        'days_left':   days_left,
    })


@merchant_required
@require_POST
def cancel_application(request, pk):
    app = get_object_or_404(Application, pk=pk, merchant=request.user, status=Application.Status.PENDING)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if not request.POST.get('confirmed'):
            return JsonResponse({'success': False, 'error': 'Confirmation required.'})
    app.status       = Application.Status.CANCELLED
    app.save(update_fields=['status'])
    app.booth.status = Booth.Status.AVAILABLE
    app.booth.save(update_fields=['status'])
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    messages.success(request, 'Reservation cancelled.')
    return redirect('merchant:reservations')


@merchant_required
@require_POST
def submit_second_payment(request, pk):
    app = get_object_or_404(Application, pk=pk, merchant=request.user,
                            status=Application.Status.APPROVED,
                            payment_option_chosen='half')
    if app.receipt_image_2:
        return JsonResponse({'success': False, 'error': 'Second payment already submitted.'})
    img = request.FILES.get('receipt_image_2')
    if not img:
        return JsonResponse({'success': False, 'error': 'Please upload your receipt image.'})
    app.receipt_image_2 = img
    app.save(update_fields=['receipt_image_2', 'updated_at'])
    if app.event.organizer:
        create_notification(
            recipient   = app.event.organizer,
            notif_type  = 'PAY_UPDATE',
            title       = 'Second Payment Submitted',
            message     = (
                f'{app.merchant_name or app.merchant.username} submitted their second payment '
                f'for {app.booth.display_name} at {app.event.title}.'
            ),
            application = app,
        )
    return JsonResponse({'success': True})


# ── Organizer views ───────────────────────────────────────────────────────────

@organizer_required
def organizer_reservation_list(request):
    apps   = (Application.objects
              .select_related('merchant', 'event', 'booth')
              .order_by('-applied_at'))
    status = request.GET.get('status', '')
    q      = request.GET.get('q', '')
    if status:
        apps = apps.filter(status=status)
    if q:
        apps = apps.filter(
            Q(merchant_name__icontains=q) |
            Q(merchant__username__icontains=q) |
            Q(booth__label__icontains=q) |
            Q(event__title__icontains=q)
        )
    paginator = Paginator(apps, 10)
    page_obj  = paginator.get_page(request.GET.get('page'))
    return render(request, 'organizer/reservation_list.html', {
        'page_obj':       page_obj,
        'status':         status,
        'q':              q,
        'status_choices': Application.Status.choices,
    })


@organizer_required
def event_applications(request, event_slug):
    event = get_object_or_404(Event, slug=event_slug)
    apps  = Application.objects.filter(event=event).select_related('merchant', 'booth')
    status = request.GET.get('status', '')
    if status:
        apps = apps.filter(status=status)
    return render(request, 'reservations/event_applications.html', {
        'event': event, 'applications': apps, 'status': status,
        'status_choices': Application.Status.choices,
    })


@organizer_required
def application_detail_json(request, pk):
    app = get_object_or_404(Application, pk=pk)
    data = {
        'id':                     app.id,
        'status':                 app.status,
        'is_disabled':            app.is_disabled,
        'merchant_name':          app.merchant_name or app.merchant.get_full_name() or app.merchant.username,
        'merchant_phone':         app.merchant_phone,
        'merchant_email':         app.merchant_email,
        'merchant_facebook':      app.merchant_facebook,
        'event_title':            app.event.title,
        'booth_label':            app.booth.display_name,
        'booth_price':            str(app.booth.price),
        'payment_option_chosen':  app.payment_option_chosen,
        'payment_status':         app.payment_status,
        'first_payment_amount':   str(app.first_payment_amount),
        'second_payment_amount':  str(app.second_payment_amount) if app.second_payment_amount else '',
        'second_payment_deadline':str(app.second_payment_deadline) if app.second_payment_deadline else '',
        'receipt_image_1_url':    request.build_absolute_uri(app.receipt_image_1.url) if app.receipt_image_1 else '',
        'receipt_image_2_url':    request.build_absolute_uri(app.receipt_image_2.url) if app.receipt_image_2 else '',
        'business_name':          app.business_name,
        'product_description':    app.product_description,
        'admin_notes':            app.admin_notes,
        'organizer_notes':        app.organizer_notes,
        'applied_at':             app.applied_at.strftime('%b %d, %Y %H:%M'),
        'confirmed_at':           app.confirmed_at.strftime('%b %d, %Y %H:%M') if app.confirmed_at else '',
    }
    return JsonResponse(data)


@organizer_required
@require_POST
def approve_application(request, pk):
    app = get_object_or_404(Application, pk=pk)
    app.admin_notes  = request.POST.get('admin_notes', app.admin_notes)
    app.status       = Application.Status.APPROVED
    app.confirmed_at = timezone.now()
    app.payment_status = (
        Application.PaymentStatus.PARTIAL if app.payment_option_chosen == 'half'
        else Application.PaymentStatus.PAID
    )
    app.save(update_fields=['status', 'confirmed_at', 'payment_status', 'admin_notes'])
    app.booth.status = Booth.Status.RESERVED
    app.booth.save(update_fields=['status'])
    create_notification(
        recipient   = app.merchant,
        notif_type  = 'APP_UPDATE',
        title       = 'Reservation Approved!',
        message     = (
            f'Your reservation for {app.booth.display_name} at {app.event.title} '
            f'has been approved. Check your confirmation for organizer contact details.'
        ),
        application = app,
    )
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'new_status': app.status})
    messages.success(request, 'Reservation approved.')
    return redirect('organizer:reservation_list')


@organizer_required
@require_POST
def deny_application(request, pk):
    app = get_object_or_404(Application, pk=pk)
    app.admin_notes = request.POST.get('admin_notes', '').strip()
    app.status      = Application.Status.DENIED
    app.save(update_fields=['status', 'admin_notes'])
    app.booth.status = Booth.Status.AVAILABLE
    app.booth.save(update_fields=['status'])
    create_notification(
        recipient   = app.merchant,
        notif_type  = 'APP_UPDATE',
        title       = 'Reservation Denied',
        message     = (
            f'Your reservation for {app.booth.display_name} at {app.event.title} '
            f'was not approved. Reason: {app.admin_notes or "No reason provided."}'
        ),
        application = app,
    )
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'new_status': app.status})
    messages.success(request, 'Reservation denied.')
    return redirect('organizer:reservation_list')


@organizer_required
@require_POST
def reject_application(request, pk):
    """Legacy reject — keep for backward compat."""
    app = get_object_or_404(Application, pk=pk)
    app.organizer_notes = request.POST.get('reason', '')
    app.status          = Application.Status.REJECTED
    app.save(update_fields=['status', 'organizer_notes'])
    app.booth.status = Booth.Status.AVAILABLE
    app.booth.save(update_fields=['status'])
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'new_status': app.status})
    messages.success(request, 'Application rejected.')
    return redirect('organizer:reservation_list')


@organizer_required
@require_POST
def request_resubmission(request, pk):
    app = get_object_or_404(Application, pk=pk)
    app.admin_notes = request.POST.get('admin_notes', '').strip()
    app.save(update_fields=['admin_notes'])
    create_notification(
        recipient   = app.merchant,
        notif_type  = 'PAY_UPDATE',
        title       = 'Receipt Resubmission Requested',
        message     = (
            f'The organizer has requested that you resubmit your payment receipt '
            f'for {app.booth.display_name} at {app.event.title}. '
            f'Note: {app.admin_notes or "Please re-upload a clearer image."}'
        ),
        application = app,
    )
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    messages.info(request, 'Resubmission request sent.')
    return redirect('organizer:reservation_list')


@organizer_required
@require_POST
def approve_second_payment(request, pk):
    app = get_object_or_404(Application, pk=pk, payment_option_chosen='half')
    app.payment_status = Application.PaymentStatus.PAID
    app.status         = Application.Status.COMPLETED
    app.save(update_fields=['payment_status', 'status'])
    create_notification(
        recipient   = app.merchant,
        notif_type  = 'PAY_UPDATE',
        title       = 'Second Payment Approved — Fully Paid!',
        message     = (
            f'Your second payment for {app.booth.display_name} at {app.event.title} '
            f'has been confirmed. Your reservation is now complete!'
        ),
        application = app,
    )
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'new_status': app.status})
    messages.success(request, 'Second payment approved. Reservation completed.')
    return redirect('organizer:reservation_list')


@organizer_required
@require_POST
def extend_deadline(request, pk):
    app          = get_object_or_404(Application, pk=pk)
    new_deadline = request.POST.get('new_deadline', '').strip()
    if not new_deadline:
        return JsonResponse({'success': False, 'error': 'Date required.'}, status=400)
    from datetime import date
    try:
        app.second_payment_deadline = date.fromisoformat(new_deadline)
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Invalid date format.'}, status=400)
    app.save(update_fields=['second_payment_deadline'])
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'new_deadline': str(app.second_payment_deadline)})
    messages.success(request, 'Deadline extended.')
    return redirect('organizer:reservation_list')


@organizer_required
@require_POST
def change_status(request, pk):
    """Organizer changes reservation status to any value — always reversible."""
    app        = get_object_or_404(Application, pk=pk)
    new_status = request.POST.get('new_status', '').strip()
    admin_notes = request.POST.get('admin_notes', '').strip()

    valid = [s[0] for s in Application.Status.choices]
    if new_status not in valid:
        return JsonResponse({'success': False, 'error': 'Invalid status.'}, status=400)

    app.status = new_status
    if admin_notes:
        app.admin_notes = admin_notes
    if new_status == Application.Status.APPROVED and not app.confirmed_at:
        app.confirmed_at   = timezone.now()
        app.payment_status = (
            Application.PaymentStatus.PARTIAL if app.payment_option_chosen == 'half'
            else Application.PaymentStatus.PAID
        )
    app.save()

    # Booth side effects
    if new_status == Application.Status.APPROVED:
        app.booth.status = Booth.Status.RESERVED
    elif new_status == Application.Status.PENDING:
        app.booth.status = Booth.Status.PENDING
    elif new_status in (Application.Status.DENIED, Application.Status.CANCELLED, Application.Status.REJECTED):
        app.booth.status = Booth.Status.AVAILABLE
    # COMPLETED → booth stays reserved
    app.booth.save(update_fields=['status'])

    msg = f'Your reservation for {app.booth.display_name} at {app.event.title} status was changed to: {app.get_status_display()}.'
    if admin_notes:
        msg += f' Note: {admin_notes}'
    create_notification(
        recipient   = app.merchant,
        notif_type  = 'APP_UPDATE',
        title       = 'Reservation Status Updated',
        message     = msg,
        application = app,
    )

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success':          True,
            'new_status':       app.status,
            'new_status_label': app.get_status_display(),
        })
    messages.success(request, f'Status changed to {app.get_status_display()}.')
    return redirect('organizer:reservation_list')


@organizer_required
@require_POST
def disable_reservation(request, pk):
    """Toggle is_disabled — hidden from merchant, booth freed when disabled."""
    app             = get_object_or_404(Application, pk=pk)
    app.is_disabled = not app.is_disabled
    app.save(update_fields=['is_disabled'])

    if app.is_disabled:
        app.booth.status = Booth.Status.AVAILABLE
        app.booth.save(update_fields=['status'])
    else:
        # Re-enable: restore booth to status-appropriate state
        if app.status == Application.Status.APPROVED:
            app.booth.status = Booth.Status.RESERVED
        else:
            app.booth.status = Booth.Status.PENDING
        app.booth.save(update_fields=['status'])

    return JsonResponse({'success': True, 'is_disabled': app.is_disabled})


@organizer_required
@require_POST
def delete_reservation(request, pk):
    """Permanently delete a reservation and free the booth."""
    app = get_object_or_404(Application, pk=pk)
    app.booth.status = Booth.Status.AVAILABLE
    app.booth.save(update_fields=['status'])
    app.delete()
    return JsonResponse({'success': True})
