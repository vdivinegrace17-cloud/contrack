from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from .models import Notification, Message
from apps.reservations.models import Application


@login_required
def unread_count(request):
    """AJAX — returns unread notification count for the nav badge."""
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'count': count})


@login_required
def notification_list_json(request):
    """AJAX — returns 10 most recent notifications and marks them read."""
    notifs = list(
        Notification.objects.filter(recipient=request.user).order_by('-created_at')[:10]
    )
    Notification.objects.filter(
        recipient=request.user, is_read=False
    ).update(is_read=True)
    data = [
        {
            'id':                     n.id,
            'title':                  n.title,
            'message':                n.message,
            'type':                   n.notification_type,
            'created_at':             n.created_at.strftime('%b %d, %Y %I:%M %p'),
            'related_application_id': n.related_application_id,
        }
        for n in notifs
    ]
    return JsonResponse({'notifications': data})


@login_required
@require_POST
def mark_all_read(request):
    """AJAX POST — marks all notifications as read."""
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})


@login_required
def message_thread(request, application_pk):
    """Shows the full message thread between organizer and merchant for an application."""
    app         = get_object_or_404(Application, pk=application_pk)
    messages_qs = Message.objects.filter(application=app).select_related('sender')
    messages_qs.filter(recipient=request.user, is_read=False).update(is_read=True)
    return render_message_thread(request, app, messages_qs)


def render_message_thread(request, app, messages_qs):
    from django.shortcuts import render
    return render(request, 'notifications/message_thread.html', {
        'application': app,
        'messages':    messages_qs,
    })


@login_required
def send_message(request, application_pk):
    """POST — sends a new message in a thread."""
    app = get_object_or_404(Application, pk=application_pk)
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            recipient = (
                app.event.organizer
                if request.user == app.merchant
                else app.merchant
            )
            Message.objects.create(
                sender=request.user,
                recipient=recipient,
                application=app,
                content=content,
            )
    return redirect('notifications:message_thread', application_pk=application_pk)
