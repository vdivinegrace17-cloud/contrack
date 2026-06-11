from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from apps.events.models import Event
from apps.reservations.models import Application
from apps.payments.models import Payment
from .decorators import organizer_required, merchant_required
from .models import User
from .forms import ConTrackLoginForm, MerchantRegistrationForm


# ── Public / Auth ─────────────────────────────────────────────────────────────

@require_http_methods(["GET"])
def landing_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard_redirect')
    return render(request, 'landing.html')


def merchant_register_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard_redirect')
    if request.method == 'POST':
        form = MerchantRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to ConTrack, {user.first_name}!")
            return redirect('merchant:dashboard')
    else:
        form = MerchantRegistrationForm()
    return render(request, 'accounts/merchant_register.html', {'form': form})


def merchant_login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard_redirect')
    if request.method == 'POST':
        form = ConTrackLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.role != User.Role.MERCHANT:
                messages.error(request, 'This login is for merchants only.')
                return render(request, 'accounts/merchant_login.html',
                              {'form': ConTrackLoginForm()})
            login(request, user)
            return redirect('merchant:dashboard')
    else:
        form = ConTrackLoginForm()
    return render(request, 'accounts/merchant_login.html', {'form': form})


def organizer_login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard_redirect')
    if request.method == 'POST':
        form = ConTrackLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.role != User.Role.ORGANIZER:
                messages.error(request, 'This login is for organizers only.')
                return render(request, 'accounts/organizer_login.html',
                              {'form': ConTrackLoginForm()})
            login(request, user)
            return redirect('organizer:dashboard')
    else:
        form = ConTrackLoginForm()
    return render(request, 'accounts/organizer_login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('accounts:landing')


# ── Dashboard routing ─────────────────────────────────────────────────────────

@login_required
def dashboard_redirect(request):
    if request.user.is_organizer:
        return redirect('organizer:dashboard')
    return redirect('merchant:dashboard')


# ── Organizer portal views ────────────────────────────────────────────────────

@organizer_required
def organizer_dashboard(request):
    context = {
        'total_merchants':  User.objects.filter(role=User.Role.MERCHANT).count(),
        'active_events':    Event.objects.filter(status='OPEN').count(),
        'pending_apps':     Application.objects.filter(status='PENDING').count(),
        'pending_payments': Payment.objects.filter(status='PENDING').count(),
        'recent_apps':      Application.objects.select_related(
                                'merchant', 'event', 'booth'
                            ).order_by('-applied_at')[:5],
        'recent_payments':  Payment.objects.select_related(
                                'application__merchant', 'application__event'
                            ).order_by('-submitted_at')[:5],
    }
    return render(request, 'organizer/dashboard.html', context)


@organizer_required
def organizer_merchant_list(request):
    users = User.objects.filter(role=User.Role.MERCHANT).order_by('-date_joined')
    q = request.GET.get('q', '')
    if q:
        users = users.filter(Q(username__icontains=q) | Q(email__icontains=q))
    return render(request, 'organizer/merchant_list.html', {'users': users, 'q': q})


@organizer_required
def organizer_toggle_merchant_active(request, pk):
    if request.method != 'POST':
        return redirect('organizer:merchant_list')
    if pk == request.user.pk:
        messages.error(request, 'You cannot deactivate your own account.')
        return redirect('organizer:merchant_list')
    user = get_object_or_404(User, pk=pk, role=User.Role.MERCHANT)
    user.is_active = not user.is_active
    user.save()
    action = 'activated' if user.is_active else 'deactivated'
    messages.success(request, f'{user.username} has been {action}.')
    return redirect('organizer:merchant_list')


@organizer_required
def organizer_profile_view(request):
    return render(request, 'accounts/profile.html', {'user': request.user})


# ── Merchant portal views ─────────────────────────────────────────────────────

@merchant_required
def merchant_dashboard(request):
    my_apps     = Application.objects.filter(
                      merchant=request.user
                  ).select_related('event', 'booth').order_by('-applied_at')[:5]
    open_events = Event.objects.filter(status='OPEN').order_by('-created_at')[:4]
    context = {
        'my_apps':     my_apps,
        'open_events': open_events,
    }
    return render(request, 'merchant/dashboard.html', context)


@merchant_required
def merchant_profile_view(request):
    return render(request, 'accounts/profile.html', {'user': request.user})
