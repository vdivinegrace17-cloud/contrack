"""
reservations/models.py
=======================
Application — submitted by a Merchant for a Booth at an Event.

Status lifecycle:
  PENDING   → APPROVED   organizer accepts and payment is confirmed
  PENDING   → DENIED     organizer declines (with admin_notes reason)
  PENDING   → WAITLISTED booth is taken, merchant is queued
  Any       → CANCELLED  merchant withdraws
  APPROVED  → COMPLETED  second payment confirmed (half/half only)

Payment is submitted WITH the initial application (receipt_image_1).
For half/half reservations a second receipt (receipt_image_2) is uploaded later.
"""

from django.conf import settings
from django.db import models


class Application(models.Model):

    class Status(models.TextChoices):
        PENDING   = 'PENDING',   'Pending'
        APPROVED  = 'APPROVED',  'Approved'
        DENIED    = 'DENIED',    'Denied'
        REJECTED  = 'REJECTED',  'Rejected'   # legacy alias kept for existing data
        CANCELLED = 'CANCELLED', 'Cancelled'
        COMPLETED = 'COMPLETED', 'Completed'

    class PaymentStatus(models.TextChoices):
        UNPAID  = 'unpaid',   'Unpaid'
        PARTIAL = 'partial',  'Partial Paid'
        PAID    = 'paid',     'Fully Paid'
        OVERDUE = 'overdue',  'Overdue'

    # ── Core relations ────────────────────────────────────────────────────────
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
    event = models.ForeignKey(
        'events.Event',
        on_delete=models.CASCADE,
        related_name='applications',
    )

    # ── Merchant application info ─────────────────────────────────────────────
    business_name       = models.CharField(max_length=200, blank=True)
    product_description = models.TextField(blank=True)
    special_requests    = models.TextField(blank=True)

    # ── Reservation status ────────────────────────────────────────────────────
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING,
    )

    # ── Payment fields (collected at reservation time) ────────────────────────
    payment_option_chosen = models.CharField(
        max_length=10,
        choices=[('full', 'Full Payment'), ('half', '50/50 Half Payment')],
        blank=True,
    )
    payment_status = models.CharField(
        max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID,
    )
    first_payment_amount    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    second_payment_amount   = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    second_payment_deadline = models.DateField(null=True, blank=True)
    receipt_image_1         = models.ImageField(upload_to='payment_proofs/', blank=True, null=True)
    receipt_image_2         = models.ImageField(upload_to='payment_proofs/', blank=True, null=True)

    # ── Merchant contact (denormalized at reservation time) ───────────────────
    merchant_name     = models.CharField(max_length=200, blank=True)
    merchant_phone    = models.CharField(max_length=30, blank=True)
    merchant_email    = models.EmailField(blank=True)
    merchant_facebook = models.URLField(blank=True)

    # ── Admin fields ──────────────────────────────────────────────────────────
    organizer_notes = models.TextField(blank=True)   # legacy internal notes
    admin_notes     = models.TextField(blank=True)   # shown to merchant on denial/resubmit
    confirmed_at    = models.DateTimeField(null=True, blank=True)
    is_disabled     = models.BooleanField(default=False)  # hidden from merchant, booth freed

    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-applied_at']
        unique_together = [['merchant', 'booth']]

    def __str__(self):
        return f'{self.merchant.username} → Booth {self.booth.booth_number} @ {self.event.title}'

    @property
    def is_half_payment(self):
        return self.payment_option_chosen == 'half'

    @property
    def days_until_second_deadline(self):
        if not self.second_payment_deadline:
            return None
        from django.utils import timezone
        delta = self.second_payment_deadline - timezone.now().date()
        return delta.days
