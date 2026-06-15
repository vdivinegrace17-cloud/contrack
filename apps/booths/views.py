import json
import uuid

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from apps.accounts.decorators import organizer_required
from .models import Booth
from apps.events.models import Event
from apps.payments.models import PaymentMethod, PaymentSettings
from apps.reservations.models import Application


def _layout_json(event):
    return [
        {
            'id':            b.id,
            'booth_number':  b.booth_number,
            'label':         b.display_name,
            'description':   b.description,
            'category':      b.category,
            'booth_type':    b.booth_type,
            'is_landmark':   b.is_landmark,
            'landmark_type': b.landmark_type,
            'color':         b.color,
            'price':         str(b.price),
            'status':        b.status,
            'grid_x':        b.grid_x,
            'grid_y':        b.grid_y,
            'grid_w':        b.grid_w,
            'grid_h':        b.grid_h,
        }
        for b in event.booths.all()
    ]


@organizer_required
def manage_booths(request, event_slug):
    event = get_object_or_404(Event, slug=event_slug)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'items':        _layout_json(event),
            'grid_columns': event.grid_columns,
            'grid_rows':    event.grid_rows,
        })
    return render(request, 'booths/grid_builder.html', {
        'event':       event,
        'layout_json': json.dumps(_layout_json(event)),
        'grid_cols':   event.grid_columns,
        'grid_rows':   event.grid_rows,
    })


@login_required
def booth_map_view(request, event_slug):
    event = get_object_or_404(Event, slug=event_slug)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'items':        _layout_json(event),
            'grid_columns': event.grid_columns,
            'grid_rows':    event.grid_rows,
        })

    ps = PaymentSettings.objects.filter(organizer=event.organizer).first()
    methods = PaymentMethod.objects.filter(organizer=event.organizer, is_active=True)

    ps_dict = {}
    if ps:
        ps_dict = {
            'payment_option':               ps.payment_option,
            'second_payment_deadline_days': ps.second_payment_deadline_days,
            'reservation_expiry_hours':     ps.reservation_expiry_hours,
            'terms_and_conditions':         ps.terms_and_conditions,
        }

    methods_list = []
    for m in methods:
        methods_list.append({
            'id':             m.id,
            'name':           m.name,
            'account_name':   m.account_name,
            'account_number': m.account_number,
            'qr_code_url':    request.build_absolute_uri(m.qr_code.url) if m.qr_code else '',
        })

    user_profile = {
        'name':     request.user.get_full_name() or request.user.username,
        'phone':    getattr(request.user, 'phone_number', ''),
        'email':    request.user.email,
        'facebook': getattr(request.user, 'facebook_url', ''),
    }

    return render(request, 'booths/booth_map.html', {
        'event':                event,
        'layout_json':          json.dumps(_layout_json(event)),
        'grid_cols':            event.grid_columns,
        'grid_rows':            event.grid_rows,
        'payment_settings_json': json.dumps(ps_dict),
        'payment_methods_json':  json.dumps(methods_list),
        'user_profile_json':     json.dumps(user_profile),
    })


@organizer_required
def get_layout(request, event_slug):
    event = get_object_or_404(Event, slug=event_slug)
    return JsonResponse({
        'grid_columns': event.grid_columns,
        'grid_rows':    event.grid_rows,
        'items':        _layout_json(event),
    })


@organizer_required
@require_POST
def save_layout(request, event_slug):
    event = get_object_or_404(Event, slug=event_slug)
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError) as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

    Event.objects.filter(pk=event.pk).update(
        grid_columns=data.get('grid_columns', event.grid_columns),
        grid_rows=data.get('grid_rows', event.grid_rows),
    )

    # Collect IDs of booths locked by active reservations — never allow editing or deleting them
    protected_ids = set(
        event.booths.filter(
            status__in=[Booth.Status.RESERVED, Booth.Status.PENDING],
            is_landmark=False,
        ).values_list('id', flat=True)
    )

    incoming_ids = set(protected_ids)  # protected booths always survive the delete sweep
    protected_labels = []

    for item in data.get('items', []):
        item_id = item.get('id')

        if item_id and item_id in protected_ids:
            # Skip all field updates for this booth — it has an active reservation
            protected_labels.append(item.get('label') or f'#{item_id}')
            continue

        if item_id:
            booth = get_object_or_404(Booth, pk=item_id, event=event)
        else:
            booth = Booth(event=event)
            is_lm = item.get('is_landmark', False)
            if is_lm:
                booth.booth_number = f"lm-{uuid.uuid4().hex[:8]}"
            else:
                booth.booth_number = item.get('booth_number') or f"slot-{item['grid_x']}-{item['grid_y']}"

        booth.label         = item.get('label', '')
        booth.description   = item.get('description', '')
        booth.is_landmark   = item.get('is_landmark', False)
        booth.landmark_type = item.get('landmark_type', '')
        booth.color         = item.get('color', '')
        booth.booth_type    = item.get('booth_type', 'BOOTH')
        booth.category      = item.get('category', 'OTHER')
        booth.price         = 0 if booth.is_landmark else (item.get('price') or 0)
        booth.status        = item.get('status', 'AVAILABLE')
        booth.grid_x        = item['grid_x']
        booth.grid_y        = item['grid_y']
        booth.grid_w        = item['grid_w']
        booth.grid_h        = item['grid_h']
        booth.save()
        incoming_ids.add(booth.id)

    event.booths.exclude(pk__in=incoming_ids).delete()

    response = {'success': True, 'items': _layout_json(event)}
    if protected_labels:
        response['warning'] = (
            f"{len(protected_labels)} booth(s) with active reservations were not modified: "
            + ', '.join(protected_labels)
        )
    return JsonResponse(response)


@organizer_required
@require_POST
def delete_layout_item(request, event_slug, item_id):
    event = get_object_or_404(Event, slug=event_slug)
    booth = get_object_or_404(Booth, pk=item_id, event=event)
    if not booth.is_landmark and booth.status in (Booth.Status.RESERVED, Booth.Status.PENDING):
        return JsonResponse({
            'success': False,
            'error': 'This booth has an active reservation and cannot be deleted. Manage it through Reservations.',
        }, status=400)
    booth.delete()
    return JsonResponse({'success': True})


@organizer_required
@require_POST
def delete_booth(request, booth_id):
    booth = get_object_or_404(Booth, pk=booth_id)
    booth.delete()
    return JsonResponse({'success': True})


@organizer_required
@require_POST
def clear_booths(request, event_slug):
    event = get_object_or_404(Event, slug=event_slug)
    event.booths.all().delete()
    return JsonResponse({'success': True})


@organizer_required
def booth_reservation_info(request, booth_id):
    booth = get_object_or_404(Booth, pk=booth_id)
    app = (
        Application.objects
        .filter(booth=booth, status__in=['PENDING', 'APPROVED', 'COMPLETED'])
        .select_related('merchant')
        .order_by('-applied_at')
        .first()
    )

    data = {
        'booth_label':  booth.display_name,
        'booth_type':   booth.get_booth_type_display(),
        'booth_price':  str(booth.price),
        'booth_status': booth.status,
    }

    if app:
        data.update({
            'application_pk':  app.pk,
            'merchant_name':   app.merchant_name or app.merchant.get_full_name() or app.merchant.username,
            'merchant_phone':  app.merchant_phone or '',
            'merchant_email':  app.merchant_email or '',
            'merchant_facebook': app.merchant_facebook or '',
            'applied_at':      app.applied_at.strftime('%b %d, %Y %I:%M %p'),
            'confirmed_at':    app.confirmed_at.strftime('%b %d, %Y %I:%M %p') if app.confirmed_at else None,
            'payment_option':  app.payment_option_chosen or 'full',
            'payment_status':  app.payment_status or 'unpaid',
            'admin_notes':     app.admin_notes or '',
            'status':          app.status,
        })

    return JsonResponse(data)
