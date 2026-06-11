"""
booths/views.py — Floor plan upload/tagging (organizer) and floor plan viewer (merchant).
"""
import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST

from apps.accounts.decorators import organizer_required
from .models import FloorPlan, Booth
from apps.events.models import Event


@login_required
def floor_plan_view(request, event_slug):
    """Interactive floor plan — accessible to any authenticated user."""
    event      = get_object_or_404(Event, slug=event_slug)
    floor_plan = get_object_or_404(FloorPlan, event=event)
    booths     = floor_plan.booths.all()

    booths_json = json.dumps([
        {
            'id':           b.id,
            'booth_number': b.booth_number,
            'label':        b.display_name,
            'category':     b.get_category_display(),
            'price':        str(b.price),
            'x_percent':    float(b.x_percent),
            'y_percent':    float(b.y_percent),
            'status':       b.status,
            'color':        b.marker_color,
        }
        for b in booths
    ])

    return render(request, 'booths/floor_plan.html', {
        'event':       event,
        'floor_plan':  floor_plan,
        'booths_json': booths_json,
    })


# ── Organizer: floor plan management ─────────────────────────────────────────

@organizer_required
def upload_floor_plan(request, event_slug):
    """Organizer uploads a floor plan image for an event."""
    event = get_object_or_404(Event, slug=event_slug)
    # TODO: FloorPlanUploadForm — image field
    #       On save: use PIL.Image.open(file).size to get natural_width/height
    return render(request, 'booths/upload_floor_plan.html', {'event': event})


@organizer_required
def booth_tagger(request, event_slug):
    """Organizer's interactive floor plan tagger."""
    event      = get_object_or_404(Event, slug=event_slug)
    floor_plan = get_object_or_404(FloorPlan, event=event)
    booths     = floor_plan.booths.all()

    booths_json = json.dumps([
        {
            'id':           b.id,
            'booth_number': b.booth_number,
            'label':        b.label,
            'category':     b.category,
            'price':        str(b.price),
            'x_percent':    float(b.x_percent),
            'y_percent':    float(b.y_percent),
            'status':       b.status,
        }
        for b in booths
    ])

    return render(request, 'booths/booth_tagger.html', {
        'event':       event,
        'floor_plan':  floor_plan,
        'booths_json': booths_json,
    })


@organizer_required
@require_POST
def save_booth(request, event_slug):
    """AJAX — organizer places or moves a booth marker."""
    event      = get_object_or_404(Event, slug=event_slug)
    floor_plan = get_object_or_404(FloorPlan, event=event)

    try:
        data     = json.loads(request.body)
        booth_id = data.get('id')

        if booth_id:
            booth = get_object_or_404(Booth, pk=booth_id, floor_plan=floor_plan)
        else:
            booth = Booth(floor_plan=floor_plan)

        booth.booth_number = data['booth_number']
        booth.label        = data.get('label', '')
        booth.category     = data.get('category', Booth.Category.OTHER)
        booth.price        = data.get('price', 0)
        booth.x_percent    = data['x_percent']
        booth.y_percent    = data['y_percent']
        booth.save()

        return JsonResponse({'success': True, 'id': booth.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@organizer_required
@require_POST
def delete_booth(request, booth_id):
    """AJAX — organizer removes a booth marker."""
    booth = get_object_or_404(Booth, pk=booth_id)
    booth.delete()
    return JsonResponse({'success': True})
