from datetime import date

from django.core.management.base import BaseCommand

from apps.notifications.utils import create_notification
from apps.reservations.models import Application


class Command(BaseCommand):
    help = 'Flag half-payment reservations whose second-payment deadline has passed.'

    def handle(self, *args, **options):
        overdue = Application.objects.filter(
            payment_option_chosen='half',
            status=Application.Status.APPROVED,
            second_payment_deadline__lt=date.today(),
            receipt_image_2='',
            payment_status=Application.PaymentStatus.PARTIAL,
        ).select_related('merchant', 'event', 'booth')

        count = 0
        for app in overdue:
            app.payment_status = Application.PaymentStatus.OVERDUE
            app.save(update_fields=['payment_status'])

            if app.event.organizer:
                create_notification(
                    recipient   = app.event.organizer,
                    notif_type  = 'PAY_UPDATE',
                    title       = 'Second Payment Overdue',
                    message     = (
                        f'{app.merchant_name or app.merchant.username} has missed the second '
                        f'payment deadline for {app.booth.display_name} at {app.event.title}.'
                    ),
                    application = app,
                )

            create_notification(
                recipient   = app.merchant,
                notif_type  = 'PAY_UPDATE',
                title       = 'Second Payment Overdue',
                message     = (
                    f'Your second payment for {app.booth.display_name} at {app.event.title} '
                    f'is overdue. Please contact the organizer immediately.'
                ),
                application = app,
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(f'Flagged {count} overdue second payment(s).'))
