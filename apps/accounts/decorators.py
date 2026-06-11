from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def organizer_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_organizer:
            return redirect('accounts:dashboard_redirect')
        return view_func(request, *args, **kwargs)
    return wrapper


def merchant_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_merchant:
            return redirect('accounts:dashboard_redirect')
        return view_func(request, *args, **kwargs)
    return wrapper
