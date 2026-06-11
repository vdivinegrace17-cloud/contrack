"""
Merchant portal URL configuration.
All routes require @merchant_required (enforced at the view level).
Mounted at /merchant/ in the root urls.py.
"""

from django.urls import path

from apps.accounts.views import merchant_dashboard, merchant_profile_view
from apps.events.views import event_list, event_detail
from apps.booths.views import floor_plan_view
from apps.reservations.views import (
    my_applications,
    application_detail,
    cancel_application,
    apply_for_booth,
)
from apps.payments.views import submit_payment, payment_detail

app_name = 'merchant'

urlpatterns = [
    # Dashboard
    path('', merchant_dashboard, name='dashboard'),

    # Browse events
    path('events/',             event_list,       name='event_list'),
    path('events/<slug:slug>/', event_detail,     name='event_detail'),
    path('events/<slug:event_slug>/map/', floor_plan_view, name='floor_plan'),

    # Reservations
    path('reservations/',                        my_applications,     name='reservations'),
    path('reservations/<int:pk>/',               application_detail,  name='application_detail'),
    path('reservations/<int:pk>/cancel/',        cancel_application,  name='cancel_application'),
    path('reservations/apply/<int:booth_id>/',   apply_for_booth,     name='apply'),

    # Payments
    path('payments/submit/<int:application_pk>/', submit_payment, name='submit_payment'),
    path('payments/<int:pk>/',                    payment_detail, name='payment_detail'),

    # Profile
    path('profile/', merchant_profile_view, name='profile'),
]
