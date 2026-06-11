"""
notifications/views.py — Inbox and messaging.
"""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect

from .models import Notification, Message
from apps.reservations.models import Application


@login_required
def notification_inbox(request):
    """User's notification list, newest first."""
    notifs = Notification.objects.filter(recipient=request.user)
    # Mark all as read on visit
    notifs.filter(is_read=False).update(is_read=True)
    return render(request, 'notifications/inbox.html', {'notifications': notifs})


@login_required
def unread_count(request):
    """AJAX — returns unread notification count for the nav badge."""
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'count': count})


@login_required
def message_thread(request, application_pk):
    """
    Shows the full message thread between organizer and merchant
    for a specific application.
    """
    app      = get_object_or_404(Application, pk=application_pk)
    messages_qs = Message.objects.filter(application=app).select_related('sender')
    # Mark incoming messages as read
    messages_qs.filter(recipient=request.user, is_read=False).update(is_read=True)

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
            # Determine recipient: if sender is merchant, recipient is event organizer; vice versa
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
            # TODO: create a Notification for the recipient
    return redirect('notifications:message_thread', application_pk=application_pk)
