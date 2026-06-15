from .models import Notification


def create_notification(recipient, notif_type, title, message, application=None):
    Notification.objects.create(
        recipient=recipient,
        notification_type=notif_type,
        title=title,
        message=message,
        related_application=application,
    )
