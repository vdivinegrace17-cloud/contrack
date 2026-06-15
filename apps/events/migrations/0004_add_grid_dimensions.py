from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0003_remove_lat_lng'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='grid_columns',
            field=models.PositiveSmallIntegerField(default=24),
        ),
        migrations.AddField(
            model_name='event',
            name='grid_rows',
            field=models.PositiveSmallIntegerField(default=18),
        ),
    ]
