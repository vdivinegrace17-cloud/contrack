from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Event(models.Model):

    class EventType(models.TextChoices):
        CONVENTION  = 'CONVENTION',  'Convention'
        FESTIVAL    = 'FESTIVAL',    'Festival'
        FAIRE       = 'FAIRE',       'Faire'
        BAZAAR      = 'BAZAAR',      'Bazaar'
        MARKET      = 'MARKET',      'Market'
        TRADE_SHOW  = 'TRADE_SHOW',  'Trade Show'
        OTHER       = 'OTHER',       'Other'

    class Status(models.TextChoices):
        DRAFT      = 'DRAFT',      'Draft'           # Not visible to merchants
        OPEN       = 'OPEN',       'Open'            # Accepting applications
        CLOSED     = 'CLOSED',     'Closed'          # Applications closed
        ONGOING    = 'ONGOING',    'Ongoing'         # Event is happening now
        COMPLETED  = 'COMPLETED',  'Completed'       # Event is over
        CANCELLED  = 'CANCELLED',  'Cancelled'

    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='events',
        limit_choices_to={'role': 'ORGANIZER'},
    )

    title      = models.CharField(max_length=200)
    slug       = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField()
    event_type  = models.CharField(max_length=20, choices=EventType.choices, default=EventType.OTHER)
    banner_image = models.ImageField(upload_to='event_banners/', blank=True, null=True)

    # Event schedule
    start_date = models.DateTimeField()
    end_date   = models.DateTimeField()

    # Application window
    application_open_date  = models.DateTimeField()
    application_close_date = models.DateTimeField()

    # Venue information
    venue_name   = models.CharField(max_length=200)
    address      = models.TextField()
    grid_columns = models.PositiveSmallIntegerField(default=24)
    grid_rows    = models.PositiveSmallIntegerField(default=18)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def is_accepting_applications(self):
        from django.utils import timezone
        now = timezone.now()
        return (
            self.status == self.Status.OPEN and
            self.application_open_date <= now <= self.application_close_date
        )

    @property
    def has_booths(self):
        return self.booths.filter(is_landmark=False).exists()
