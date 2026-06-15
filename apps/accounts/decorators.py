from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect


def _ajax_login_required(view_func):
    """Login-required that returns JSON 403 for AJAX requests instead of redirect."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'session_expired'}, status=403)
            return redirect('accounts:landing')
        return view_func(request, *args, **kwargs)
    return wrapper


def organizer_required(view_func):
    @wraps(view_func)
    @_ajax_login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_organizer:
            return redirect('accounts:dashboard_redirect')
        return view_func(request, *args, **kwargs)
    return wrapper


def merchant_required(view_func):
    @wraps(view_func)
    @_ajax_login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_merchant:
            return redirect('accounts:dashboard_redirect')
        return view_func(request, *args, **kwargs)
    return wrapper
