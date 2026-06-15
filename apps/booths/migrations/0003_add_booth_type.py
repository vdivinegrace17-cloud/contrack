from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booths', '0002_booth_grid_system'),
    ]

    operations = [
        migrations.AddField(
            model_name='booth',
            name='booth_type',
            field=models.CharField(
                choices=[('TABLE', 'Table'), ('STALL', 'Stall'), ('BOOTH', 'Booth')],
                default='BOOTH',
                max_length=10,
            ),
        ),
    ]
