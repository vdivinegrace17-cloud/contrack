"""
booths/models.py
=================
Two models work together here:

  FloorPlan  — an image uploaded by the organizer for a specific event.
  Booth      — a single table/booth tagged onto that floor plan image.

How the floor plan works with Leaflet.js:
  - The organizer uploads a floor plan image (JPG/PNG of the hall/venue layout).
  - In the organizer dashboard, a Leaflet map using L.CRS.Simple is loaded
    with the floor plan image as the base layer via L.imageOverlay().
  - The organizer clicks on the image to place booth markers. Each click
    records the x_percent and y_percent (0.0–100.0) of the click position
    relative to the image dimensions. Storing percentages keeps booth
    positions accurate even if the image is displayed at different sizes.
  - Merchants see the same floor plan with color-coded markers:
      green  = AVAILABLE
      yellow = PENDING (someone applied but not yet approved)
      red    = RESERVED (approved)
      gray   = UNAVAILABLE (blocked by organizer)
  - Clicking an available (green) marker opens the reservation form for that booth.
"""

from django.db import models


class FloorPlan(models.Model):
    """
    One floor plan image per event.
    The natural dimensions are stored so the JS can correctly
    convert pixel coordinates to percentage-based positions.
    """
    event = models.OneToOneField(
        'events.Event',
        on_delete=models.CASCADE,
        related_name='floor_plan',
    )
    image = models.ImageField(
        upload_to='floor_plans/',
        help_text='Upload a clear image of the venue/hall layout.',
    )
    # Stored on upload (via Pillow) — used by JS for coordinate math
    natural_width  = models.PositiveIntegerField(default=0)
    natural_height = models.PositiveIntegerField(default=0)

    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Floor Plan — {self.event.title}'


class Booth(models.Model):
    """
    A single booth or table on a floor plan.
    Position is stored as percentages so it's resolution-independent.
    """

    class Category(models.TextChoices):
        FOOD_BEVERAGE  = 'FOOD',  'Food & Beverage'
        MERCHANDISE    = 'MERCH', 'Merchandise'
        ARTS_CRAFTS    = 'ARTS',  'Arts & Crafts'
        SERVICES       = 'SERV',  'Services'
        COLLECTIBLES   = 'COLL',  'Collectibles'
        OTHER          = 'OTHER', 'Other'

    class Status(models.TextChoices):
        AVAILABLE   = 'AVAILABLE',   'Available'
        PENDING     = 'PENDING',     'Pending'     # Has an unresolved application
        RESERVED    = 'RESERVED',    'Reserved'    # Application approved
        UNAVAILABLE = 'UNAVAILABLE', 'Unavailable' # Blocked by organizer

    floor_plan = models.ForeignKey(
        FloorPlan,
        on_delete=models.CASCADE,
        related_name='booths',
    )

    booth_number = models.CharField(
        max_length=20,
        help_text='e.g. A1, B3, Table-12',
    )
    label       = models.CharField(max_length=100, blank=True, help_text='Optional display name.')
    category    = models.CharField(max_length=10, choices=Category.choices, default=Category.OTHER)
    description = models.TextField(blank=True)

    # ── Position on the floor plan image (set via Leaflet click) ──────────
    # Values are 0.0 to 100.0 (percentage of image width/height).
    x_percent = models.DecimalField(max_digits=6, decimal_places=3, default=0)
    y_percent = models.DecimalField(max_digits=6, decimal_places=3, default=0)

    # ── Physical dimensions (informational, shown to merchants) ───────────
    width_meters  = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    height_meters = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # ── Pricing ───────────────────────────────────────────────────────────
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    notes  = models.TextField(blank=True, help_text='Internal organizer notes. Not shown to merchants.')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['booth_number']
        # Booth numbers must be unique within a floor plan
        unique_together = [['floor_plan', 'booth_number']]

    def __str__(self):
        return f'Booth {self.booth_number} — {self.floor_plan.event.title}'

    @property
    def display_name(self):
        return self.label if self.label else f'Booth {self.booth_number}'

    @property
    def marker_color(self):
        """Returns a CSS color string for the Leaflet marker."""
        colors = {
            self.Status.AVAILABLE:   'green',
            self.Status.PENDING:     'orange',
            self.Status.RESERVED:    'red',
            self.Status.UNAVAILABLE: 'gray',
        }
        return colors.get(self.status, 'gray')
