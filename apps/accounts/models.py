from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ORGANIZER = 'ORGANIZER', 'Organizer'
        MERCHANT  = 'MERCHANT',  'Merchant'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MERCHANT,
    )
    phone_number    = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio             = models.TextField(blank=True)
    updated_at      = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Organizers get Django admin staff access automatically
        if self.role == self.Role.ORGANIZER:
            self.is_staff = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'

    @property
    def is_organizer(self):
        return self.role == self.Role.ORGANIZER

    @property
    def is_merchant(self):
        return self.role == self.Role.MERCHANT
