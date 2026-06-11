from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

User = get_user_model()


class Command(BaseCommand):
    help = 'Create an organizer account (internal use only — no public registration)'

    def add_arguments(self, parser):
        parser.add_argument('--username', required=True)
        parser.add_argument('--email',    required=True)
        parser.add_argument('--password', required=True)
        parser.add_argument('--name',     default='', help='First name / display name')

    def handle(self, *args, **options):
        username = options['username']
        email    = options['email']
        password = options['password']
        name     = options['name']

        if User.objects.filter(username=username).exists():
            raise CommandError(f"User '{username}' already exists.")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=name,
            role='ORGANIZER',
            is_staff=True,
        )
        self.stdout.write(self.style.SUCCESS(
            f"Organizer '{user.username}' created successfully. "
            f"Login at /organizer/login/"
        ))
