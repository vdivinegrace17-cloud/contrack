"""
payments/models.py
==================
Payments are fully external (GCash, bank transfer, etc.).
Merchants submit a proof of payment image and a reference number.
The Organizer manually verifies and marks it as VERIFIED or REJECTED.

No payment gateway integration is needed — 100% free to build and run.
"""

from django.conf import settings
from django.db import models


class Payment(models.Model):

    class Status(models.TextChoices):
        PENDING  = 'PENDING',  'Pending Verification'
        VERIFIED = 'VERIFIED', 'Verified'
        REJECTED = 'REJECTED', 'Rejected'

    # Each approved application can have one payment submission
    application = models.OneToOneField(
        'reservations.Application',
        on_delete=models.CASCADE,
        related_name='payment',
    )

    # What the merchant declares they paid (for reference/comparison)
    amount_declared  = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method   = models.CharField(
        max_length=100,
        help_text='e.g. GCash, BPI Bank Transfer, Maya, Cash',
    )
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        help_text='Transaction or reference number from the payment.',
    )
    proof_image = models.ImageField(
        upload_to='payment_proofs/',
        help_text='Screenshot or photo of the payment confirmation.',
    )

    status       = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    submitted_at = models.DateTimeField(auto_now_add=True)

    # Filled in when an organizer verifies or rejects
    verified_by      = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='verified_payments',
    )
    verified_at      = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    def __str__(self):
        return f'Payment for {self.application} [{self.get_status_display()}]'
