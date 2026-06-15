from django.core.management.base import BaseCommand

from apps.booths.models import Booth
from apps.payments.models import Payment
from apps.reservations.models import Application


class Command(BaseCommand):
    help = 'Delete all test reservations and payments, reset all booth statuses to AVAILABLE.'

    def handle(self, *args, **options):
        app_count = Application.objects.count()
        Application.objects.all().delete()
        self.stdout.write(f'  Deleted {app_count} Application(s).')

        pay_count = Payment.objects.count()
        Payment.objects.all().delete()
        self.stdout.write(f'  Deleted {pay_count} Payment(s).')

        booth_count = Booth.objects.exclude(status=Booth.Status.AVAILABLE).count()
        Booth.objects.all().update(status=Booth.Status.AVAILABLE)
        self.stdout.write(f'  Reset {booth_count} booth(s) to AVAILABLE.')

        self.stdout.write(self.style.SUCCESS('Test data cleared. All booths are now available.'))
