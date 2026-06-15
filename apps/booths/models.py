from django.db import models


class Booth(models.Model):

    class Category(models.TextChoices):
        FOOD_BEVERAGE = 'FOOD',  'Food & Beverage'
        MERCHANDISE   = 'MERCH', 'Merchandise'
        ARTS_CRAFTS   = 'ARTS',  'Arts & Crafts'
        SERVICES      = 'SERV',  'Services'
        COLLECTIBLES  = 'COLL',  'Collectibles'
        OTHER         = 'OTHER', 'Other'

    class BoothType(models.TextChoices):
        TABLE = 'TABLE', 'Table'
        STALL = 'STALL', 'Stall'
        BOOTH = 'BOOTH', 'Booth'
        KIOSK = 'KIOSK', 'Kiosk'

    class Status(models.TextChoices):
        AVAILABLE   = 'AVAILABLE',   'Available'
        PENDING     = 'PENDING',     'Pending'
        RESERVED    = 'RESERVED',    'Reserved'
        UNAVAILABLE = 'UNAVAILABLE', 'Unavailable'

    event = models.ForeignKey(
        'events.Event',
        on_delete=models.CASCADE,
        related_name='booths',
    )

    booth_number = models.CharField(max_length=20)
    label        = models.CharField(max_length=100, blank=True)
    category     = models.CharField(max_length=10, choices=Category.choices, default=Category.OTHER)
    booth_type   = models.CharField(max_length=10, choices=BoothType.choices, default=BoothType.BOOTH)
    description   = models.TextField(blank=True)
    is_landmark   = models.BooleanField(default=False)
    landmark_type = models.CharField(max_length=30, blank=True, choices=[
        ('entrance',       'Entrance'),
        ('exit',           'Exit'),
        ('stage',          'Stage'),
        ('restroom',       'Restroom'),
        ('food_court',     'Food Court'),
        ('emergency_exit', 'Emergency Exit'),
        ('info_desk',      'Info Desk'),
        ('parking',        'Parking'),
        ('custom',         'Custom'),
    ])
    color = models.CharField(max_length=20, blank=True)

    # Grid position (0-indexed column and row)
    grid_x = models.PositiveSmallIntegerField(default=0)
    grid_y = models.PositiveSmallIntegerField(default=0)
    # Grid span (1 = single cell)
    grid_w = models.PositiveSmallIntegerField(default=1)
    grid_h = models.PositiveSmallIntegerField(default=1)

    price  = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    notes  = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['booth_number']
        unique_together = [['event', 'booth_number']]

    def __str__(self):
        return f'Booth {self.booth_number} — {self.event.title}'

    @property
    def display_name(self):
        return self.label if self.label else f'Booth {self.booth_number}'
