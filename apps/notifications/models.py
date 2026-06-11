"""
notifications/models.py
========================
Two models:
  Notification — system-generated alerts (application status changes, payment updates, etc.)
  Message      — direct messages between an organizer and a merchant, linked to an application.
"""

from django.conf import settings
from django.db import models


class Notification(models.Model):

    class NotificationType(models.TextChoices):
        APPLICATION_UPDATE = 'APP_UPDATE', 'Application Update'
        PAYMENT_UPDATE     = 'PAY_UPDATE', 'Payment Update'
        NEW_MESSAGE        = 'MESSAGE',    'New Message'
        SYSTEM             = 'SYSTEM',     'System'

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices)
    title   = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)

    # Optional link back to the relevant application
    related_application = models.ForeignKey(
        'reservations.Application',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='notifications',
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.get_notification_type_display()}] → {self.recipient.username}'


class Message(models.Model):
    """
    Direct messages between organizer staff and a merchant,
    always in the context of a specific application.
    """
    sender    = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_messages',
    )
    # Messages are always tied to an application for context
    application = models.ForeignKey(
        'reservations.Application',
        on_delete=models.CASCADE,
        related_name='messages',
    )
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sent_at']

    def __str__(self):
        return f'{self.sender.username} → {self.recipient.username} re: {self.application}'
