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
    event_data,
    delete_event,
    publish_event,
)
from apps.booths.views import (
    manage_booths,
    get_layout,
    save_layout,
    delete_layout_item,
    delete_booth,
    clear_booths,
    booth_reservation_info,
)
from apps.reservations.views import (
    organizer_reservation_list,
    event_applications,
    approve_application,
    deny_application,
    reject_application,
    application_detail,
    application_detail_json,
    request_resubmission,
    approve_second_payment,
    extend_deadline,
    change_status,
    disable_reservation,
    delete_reservation,
)
from apps.payments.views import (
    payment_settings_view,
    payment_method_create,
    payment_method_edit,
    payment_method_delete,
    payment_method_toggle,
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
    path('events/<slug:slug>/data/',           event_data,           name='event_data'),
    path('events/<slug:slug>/publish/',        publish_event,        name='publish_event'),

    # Booth / floor-plan management (per event)
    path('events/<slug:event_slug>/booths/manage/',                 manage_booths,      name='manage_booths'),
    path('events/<slug:event_slug>/layout/',                        get_layout,         name='get_layout'),
    path('events/<slug:event_slug>/layout/save/',                   save_layout,        name='save_layout'),
    path('events/<slug:event_slug>/layout/<int:item_id>/delete/',   delete_layout_item, name='delete_layout_item'),
    path('events/<slug:event_slug>/booths/clear/',                  clear_booths,       name='clear_booths'),
    path('booths/<int:booth_id>/delete/',                           delete_booth,       name='delete_booth'),
    path('booths/<int:booth_id>/info/',                             booth_reservation_info, name='booth_reservation_info'),

    # Reservation management
    path('reservations/',                             organizer_reservation_list, name='reservation_list'),
    path('reservations/<slug:event_slug>/',           event_applications,         name='event_applications'),
    path('reservations/<int:pk>/detail/',             application_detail,         name='application_detail'),
    path('reservations/<int:pk>/detail/json/',        application_detail_json,    name='application_detail_json'),
    path('reservations/<int:pk>/approve/',            approve_application,        name='approve_application'),
    path('reservations/<int:pk>/deny/',               deny_application,           name='deny_application'),
    path('reservations/<int:pk>/reject/',             reject_application,         name='reject_application'),
    path('reservations/<int:pk>/resubmit/',           request_resubmission,       name='request_resubmission'),
    path('reservations/<int:pk>/approve-second/',     approve_second_payment,     name='approve_second_payment'),
    path('reservations/<int:pk>/extend-deadline/',    extend_deadline,            name='extend_deadline'),
    path('reservations/<int:pk>/change-status/',      change_status,              name='change_status'),
    path('reservations/<int:pk>/disable/',            disable_reservation,        name='disable_reservation'),
    path('reservations/<int:pk>/delete/',             delete_reservation,         name='delete_reservation'),

    # Payment Settings
    path('payment-settings/',                  payment_settings_view,  name='payment_settings'),
    path('payment-methods/create/',            payment_method_create,  name='payment_method_create'),
    path('payment-methods/<int:pk>/edit/',     payment_method_edit,    name='payment_method_edit'),
    path('payment-methods/<int:pk>/delete/',   payment_method_delete,  name='payment_method_delete'),
    path('payment-methods/<int:pk>/toggle/',   payment_method_toggle,  name='payment_method_toggle'),

    # Profile
    path('profile/', organizer_profile_view, name='profile'),
]
