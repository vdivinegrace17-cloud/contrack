import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST

from apps.accounts.decorators import organizer_required, merchant_required
from .models import Payment, PaymentMethod, PaymentSettings
from apps.reservations.models import Application


# ── Merchant views ────────────────────────────────────────────────────────────

@merchant_required
def submit_payment(request, application_pk):
    app = get_object_or_404(Application, pk=application_pk, merchant=request.user,
                            status=Application.Status.APPROVED)
    return render(request, 'payments/submit_payment.html', {'application': app})


@login_required
def payment_detail(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    if request.user.is_merchant and payment.application.merchant != request.user:
        return redirect('merchant:dashboard')
    return render(request, 'payments/payment_detail.html', {'payment': payment})


# ── Payment Settings views (organizer) ────────────────────────────────────────

@organizer_required
def payment_settings_view(request):
    ps, _ = PaymentSettings.objects.get_or_create(organizer=request.user)

    # Auto-seed default GCash + Maya methods if none exist yet
    if not PaymentMethod.objects.filter(organizer=request.user).exists():
        PaymentMethod.objects.bulk_create([
            PaymentMethod(organizer=request.user, name='GCash', is_active=True),
            PaymentMethod(organizer=request.user, name='Maya',  is_active=True),
        ])

    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        ps.payment_option               = request.POST.get('payment_option', ps.payment_option)
        raw_days = request.POST.get('second_payment_deadline_days', '')
        ps.second_payment_deadline_days = int(raw_days) if raw_days.strip().isdigit() else None
        raw_exp = request.POST.get('reservation_expiry_hours', '')
        ps.reservation_expiry_hours     = int(raw_exp) if raw_exp.strip().isdigit() else 24
        ps.terms_and_conditions         = request.POST.get('terms_and_conditions', ps.terms_and_conditions)
        ps.organizer_name               = request.POST.get('organizer_name', '')
        raw_phone = request.POST.get('organizer_phone', '').strip()
        import re as _re
        if raw_phone and not _re.match(r'^09\d{9}$', raw_phone):
            return JsonResponse({'success': False, 'error': 'Enter a valid Philippine mobile number (e.g., 09171234567).'}, status=400)
        ps.organizer_phone              = raw_phone
        ps.organizer_email              = request.POST.get('organizer_email', '')
        ps.organizer_facebook           = request.POST.get('organizer_facebook', '')
        ps.gc_messenger_link            = request.POST.get('gc_messenger_link', '')
        ps.save()
        return JsonResponse({'success': True})

    methods = PaymentMethod.objects.filter(organizer=request.user)
    return render(request, 'organizer/payment_settings.html', {
        'ps': ps, 'methods': methods,
    })


@organizer_required
@require_POST
def payment_method_create(request):
    m = PaymentMethod(organizer=request.user)
    m.name           = request.POST.get('name', '').strip()
    m.account_name   = request.POST.get('account_name', '').strip()
    m.account_number = request.POST.get('account_number', '').strip()
    if 'qr_code' in request.FILES:
        m.qr_code = request.FILES['qr_code']
    if not m.name:
        return JsonResponse({'success': False, 'error': 'Name is required.'}, status=400)
    m.save()
    return JsonResponse({'success': True, 'method': _method_dict(request, m)})


@organizer_required
@require_POST
def payment_method_edit(request, pk):
    m = get_object_or_404(PaymentMethod, pk=pk, organizer=request.user)
    m.name           = request.POST.get('name', m.name).strip()
    m.account_name   = request.POST.get('account_name', m.account_name).strip()
    m.account_number = request.POST.get('account_number', m.account_number).strip()
    if 'qr_code' in request.FILES:
        m.qr_code = request.FILES['qr_code']
    m.save()
    return JsonResponse({'success': True, 'method': _method_dict(request, m)})


@organizer_required
@require_POST
def payment_method_delete(request, pk):
    m = get_object_or_404(PaymentMethod, pk=pk, organizer=request.user)
    m.delete()
    return JsonResponse({'success': True})


@organizer_required
@require_POST
def payment_method_toggle(request, pk):
    m = get_object_or_404(PaymentMethod, pk=pk, organizer=request.user)
    m.is_active = not m.is_active
    m.save(update_fields=['is_active'])
    return JsonResponse({'success': True, 'is_active': m.is_active})


def _method_dict(request, m):
    return {
        'id':             m.id,
        'name':           m.name,
        'account_name':   m.account_name,
        'account_number': m.account_number,
        'qr_code_url':    request.build_absolute_uri(m.qr_code.url) if m.qr_code else '',
        'is_active':      m.is_active,
    }
