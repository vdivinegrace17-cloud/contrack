"""
reservations/models.py
=======================
An Application is submitted by a Merchant for a specific Booth at an Event.
The Organizer of that event reviews it and sets the status.

Status lifecycle:
  PENDING → APPROVED  (organizer accepts the merchant)
  PENDING → REJECTED  (organizer declines)
  PENDING → WAITLISTED (booth is taken, merchant is queued)
  Any     → CANCELLED  (merchant withdraws their own application)

When an Application is APPROVED, the related Booth's status is set to RESERVED.
When an Application is REJECTED or CANCELLED, the Booth goes back to AVAILABLE.
"""

from django.conf import settings
from django.db import models


class Application(models.Model):

    class Status(models.TextChoices):
        PENDING    = 'PENDING',    'Pending'
        APPROVED   = 'APPROVED',   'Approved'
        REJECTED   = 'REJECTED',   'Rejected'
        WAITLISTED = 'WAITLISTED', 'Waitlisted'
        CANCELLED  = 'CANCELLED',  'Cancelled'

    merchant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='applications',
        limit_choices_to={'role': 'MERCHANT'},
    )
    booth = models.ForeignKey(
        'booths.Booth',
        on_delete=models.CASCADE,
        related_name='applications',
    )
    # Denormalized for easy querying without joining through booth → floor_plan → event
    event = models.ForeignKey(
        'events.Event',
        on_delete=models.CASCADE,
        related_name='applications',
    )

    # Merchant's self-reported info for this application
    business_name       = models.CharField(max_length=200)
    product_description = models.TextField(help_text='Briefly describe what you will be selling.')
    special_requests    = models.TextField(blank=True, help_text='Any special setup needs or requests.')

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    # Organizer-only field: internal notes visible only in organizer dashboard
    organizer_notes = models.TextField(blank=True)

    applied_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-applied_at']
        # A merchant can only have one active application per booth
        unique_together = [['merchant', 'booth']]

    def __str__(self):
        return f'{self.merchant.username} → Booth {self.booth.booth_number} @ {self.event.title}'
