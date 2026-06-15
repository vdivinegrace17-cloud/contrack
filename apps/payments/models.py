"""
payments/models.py
==================
Payment — legacy model for manual proof submission after approval.
PaymentMethod — organizer-configured payment options (GCash, Maya, custom).
PaymentSettings — per-organizer payment terms, contact info, and T&C.
"""

from django.conf import settings
from django.db import models


DEFAULT_TERMS = (
    "Welcome to CONTRACK. By reserving a booth or stall through this platform, "
    "you agree to the following terms:\n\n"
    "1. Reservation is only confirmed upon review and approval of your payment proof "
    "by the organizer.\n\n"
    "2. Full payment must be completed before the event date. For 50/50 arrangements, "
    "the second payment must be submitted by the stated deadline.\n\n"
    "3. Failure to submit payment proof within 24 hours of reservation will result in "
    "automatic cancellation of your slot.\n\n"
    "4. Refunds are subject to the organizer's discretion and cancellation policy.\n\n"
    "5. The organizer reserves the right to deny any reservation without obligation to "
    "disclose a reason.\n\n"
    "6. Slot assignments are final once confirmed. Requests for slot changes are subject "
    "to availability.\n\n"
    "For concerns, contact the organizer directly via the details provided in your confirmation."
)


class Payment(models.Model):

    class Status(models.TextChoices):
        PENDING  = 'PENDING',  'Pending Verification'
        VERIFIED = 'VERIFIED', 'Verified'
        REJECTED = 'REJECTED', 'Rejected'

    application = models.OneToOneField(
        'reservations.Application',
        on_delete=models.CASCADE,
        related_name='payment',
    )

    amount_declared  = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method   = models.CharField(max_length=100)
    reference_number = models.CharField(max_length=100, blank=True)
    proof_image      = models.ImageField(upload_to='payment_proofs/')

    status       = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    submitted_at = models.DateTimeField(auto_now_add=True)

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


class PaymentMethod(models.Model):
    organizer      = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payment_methods',
        limit_choices_to={'role': 'ORGANIZER'},
    )
    name           = models.CharField(max_length=100)
    account_name   = models.CharField(max_length=200, blank=True)
    account_number = models.CharField(max_length=100, blank=True)
    qr_code        = models.ImageField(upload_to='payment_qr/', blank=True, null=True)
    is_active      = models.BooleanField(default=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.organizer.username})'


class PaymentSettings(models.Model):

    OPTION_FULL     = 'full_only'
    OPTION_HALF     = 'half_half'
    OPTION_BOTH     = 'both'
    OPTION_CHOICES  = [
        (OPTION_FULL, 'Full Payment Only'),
        (OPTION_HALF, '50/50 — Half Now, Half Later'),
        (OPTION_BOTH, 'Both Options Available'),
    ]

    organizer = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payment_settings',
        limit_choices_to={'role': 'ORGANIZER'},
    )
    payment_option               = models.CharField(
        max_length=20, choices=OPTION_CHOICES, default=OPTION_FULL,
    )
    second_payment_deadline_days = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Days before the event start date that second payment is due.',
    )
    reservation_expiry_hours     = models.PositiveIntegerField(
        default=24,
        help_text='Hours the merchant has to submit payment proof before slot is released.',
    )
    terms_and_conditions         = models.TextField(default=DEFAULT_TERMS)
    organizer_name               = models.CharField(max_length=200, blank=True)
    organizer_phone              = models.CharField(max_length=30, blank=True)
    organizer_email              = models.EmailField(blank=True)
    organizer_facebook           = models.URLField(blank=True)
    gc_messenger_link            = models.URLField(blank=True)
    updated_at                   = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'PaymentSettings for {self.organizer.username}'
