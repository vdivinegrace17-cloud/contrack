"""
communications/models.py
In-system messaging and notifications:
  - Notification    : a one-way alert sent to a user (reservation updates, etc.)
  - MessageThread   : a conversation tied to a Reservation between organizer and merchant
  - Message         : a single message inside a thread
"""

from django.db import models
from apps.accounts.models import CustomUser, OrganizerOrganization, MerchantProfile
from apps.reservations.models import Reservation


class Notification(models.Model):
    """
    A one-way alert sent to a user.
    Created automatically by the system when key events occur
    (e.g. reservation approved, payment verified, org registration approved).
    """

    TYPE_RESERVATION_UPDATE = 'reservation_update'
    TYPE_PAYMENT_UPDATE     = 'payment_update'
    TYPE_NEW_MESSAGE        = 'new_message'
    TYPE_EVENT_UPDATE       = 'event_update'
    TYPE_ORG_STATUS         = 'org_status'
    TYPE_CHOICES            = [
        (TYPE_RESERVATION_UPDATE, 'Reservation Update'),
        (TYPE_PAYMENT_UPDATE,     'Payment Update'),
        (TYPE_NEW_MESSAGE,        'New Message'),
        (TYPE_EVENT_UPDATE,       'Event Update'),
        (TYPE_ORG_STATUS,         'Organization Status'),
    ]

    recipient         = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    title             = models.CharField(max_length=200)
    body              = models.TextField()
    link              = models.CharField(
        max_length=300, blank=True,
        help_text='Optional URL the notification links to (e.g. reservation detail page).',
    )
    is_read           = models.BooleanField(default=False)
    created_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @classmethod
    def send(cls, recipient, notification_type, title, body, link=''):
        """Convenience method to create a notification in one line."""
        return cls.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            body=body,
            link=link,
        )

    def mark_read(self):
        self.is_read = True
        self.save(update_fields=['is_read'])

    def __str__(self):
        return f'[{self.get_notification_type_display()}] → {self.recipient.username}: {self.title}'


class MessageThread(models.Model):
    """
    A conversation channel between one organizer and one merchant,
    optionally tied to a specific Reservation.
    """

    reservation = models.OneToOneField(
        Reservation,
        on_delete=models.CASCADE,
        related_name='message_thread',
        null=True, blank=True,
        help_text='The reservation this thread is about (if any).',
    )
    organizer   = models.ForeignKey(
        OrganizerOrganization,
        on_delete=models.CASCADE,
        related_name='message_threads',
    )
    merchant    = models.ForeignKey(
        MerchantProfile,
        on_delete=models.CASCADE,
        related_name='message_threads',
    )
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering    = ['-created_at']
        # Prevent duplicate threads for the same reservation
        unique_together = [('organizer', 'merchant', 'reservation')]

    @property
    def latest_message(self):
        return self.messages.order_by('-sent_at').first()

    @property
    def unread_count_for_organizer(self):
        return self.messages.filter(
            is_read=False,
        ).exclude(sender=self.organizer.user).count()

    @property
    def unread_count_for_merchant(self):
        return self.messages.filter(
            is_read=False,
        ).exclude(sender=self.merchant.user).count()

    def __str__(self):
        subject = f'Re: {self.reservation}' if self.reservation else 'General Inquiry'
        return f'{self.organizer.org_name} ↔ {self.merchant.business_name} | {subject}'


class Message(models.Model):
    """
    A single message inside a MessageThread.
    """

    thread     = models.ForeignKey(
        MessageThread,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender     = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='sent_messages',
    )
    content    = models.TextField()
    sent_at    = models.DateTimeField(auto_now_add=True)
    is_read    = models.BooleanField(default=False)

    class Meta:
        ordering = ['sent_at']

    def __str__(self):
        return f'{self.sender.username} @ {self.sent_at:%Y-%m-%d %H:%M}'
