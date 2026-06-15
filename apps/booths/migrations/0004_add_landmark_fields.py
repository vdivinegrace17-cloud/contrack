from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booths', '0003_add_booth_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='booth',
            name='is_landmark',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='booth',
            name='landmark_type',
            field=models.CharField(
                max_length=30,
                blank=True,
                default='',
                choices=[
                    ('entrance',       'Entrance'),
                    ('exit',           'Exit'),
                    ('stage',          'Stage'),
                    ('restroom',       'Restroom'),
                    ('food_court',     'Food Court'),
                    ('emergency_exit', 'Emergency Exit'),
                    ('info_desk',      'Info Desk'),
                    ('parking',        'Parking'),
                    ('custom',         'Custom'),
                ],
            ),
        ),
        migrations.AddField(
            model_name='booth',
            name='color',
            field=models.CharField(max_length=20, blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='booth',
            name='booth_type',
            field=models.CharField(
                max_length=10,
                choices=[
                    ('TABLE', 'Table'),
                    ('STALL', 'Stall'),
                    ('BOOTH', 'Booth'),
                    ('KIOSK', 'Kiosk'),
                ],
                default='BOOTH',
            ),
        ),
    ]
