"""
Organizer portal URL configuration.
All routes require @organizer_required (enforced at the view level).
Mounted at /organizer/ in the root urls.py.
"""

from django.urls import path

from apps.accounts.views import (
    organizer_dashboard,
    organizer_merchant_list,
    organizer_toggle_merchant_active,
    organizer_profile_view,
)
from apps.events.views import (
    organizer_event_list,
    create_event,
    edit_event,
    delete_event,
)
from apps.booths.views import (
    upload_floor_plan,
    booth_tagger,
    save_booth,
    delete_booth,
)
from apps.reservations.views import (
    organizer_reservation_list,
    event_applications,
    approve_application,
    reject_application,
    waitlist_application,
    application_detail,
)
from apps.payments.views import (
    organizer_payment_list,
    pending_payments,
    verify_payment,
    reject_payment,
)

app_name = 'organizer'

urlpatterns = [
    # Dashboard
    path('', organizer_dashboard, name='dashboard'),

    # Merchant management
    path('merchants/',                         organizer_merchant_list,          name='merchant_list'),
    path('merchants/<int:pk>/toggle/',         organizer_toggle_merchant_active, name='toggle_merchant'),

    # Event management
    path('events/',                            organizer_event_list, name='event_list'),
    path('events/create/',                     create_event,         name='create_event'),
    path('events/<slug:slug>/edit/',           edit_event,           name='edit_event'),
    path('events/<slug:slug>/delete/',         delete_event,         name='delete_event'),

    # Booth management (per event)
    path('events/<slug:event_slug>/booths/upload/',  upload_floor_plan, name='upload_floor_plan'),
    path('events/<slug:event_slug>/booths/tagger/',  booth_tagger,      name='booth_tagger'),
    path('events/<slug:event_slug>/booths/save/',    save_booth,        name='save_booth'),
    path('booths/<int:booth_id>/delete/',            delete_booth,      name='delete_booth'),

    # Reservation management
    path('reservations/',                      organizer_reservation_list,            name='reservation_list'),
    path('reservations/<slug:event_slug>/',    event_applications,                    name='event_applications'),
    path('reservations/<int:pk>/detail/',      application_detail,                    name='application_detail'),
    path('reservations/<int:pk>/approve/',     approve_application,                   name='approve_application'),
    path('reservations/<int:pk>/reject/',      reject_application,                    name='reject_application'),
    path('reservations/<int:pk>/waitlist/',    waitlist_application,                  name='waitlist_application'),

    # Payment management
    path('payments/',                          organizer_payment_list,  name='payment_list'),
    path('payments/<slug:event_slug>/pending/', pending_payments,       name='pending_payments'),
    path('payments/<int:pk>/verify/',          verify_payment,          name='verify_payment'),
    path('payments/<int:pk>/reject/',          reject_payment,          name='reject_payment'),

    # Profile
    path('profile/', organizer_profile_view, name='profile'),
]
