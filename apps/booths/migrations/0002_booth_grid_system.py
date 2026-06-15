from django.db import migrations, models
import django.db.models.deletion


def migrate_booth_event(apps, schema_editor):
    Booth = apps.get_model('booths', 'Booth')
    for booth in Booth.objects.select_related('floor_plan__event').all():
        booth.event = booth.floor_plan.event
        booth.save()


class Migration(migrations.Migration):

    dependencies = [
        ('booths', '0001_initial'),
        ('events', '0003_remove_lat_lng'),
    ]

    operations = [
        # 1. Drop old unique_together so we can modify booth fields freely
        migrations.AlterUniqueTogether(
            name='booth',
            unique_together=set(),
        ),

        # 2. Add nullable event FK (will be populated by data migration)
        migrations.AddField(
            model_name='booth',
            name='event',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='booths',
                to='events.event',
            ),
        ),

        # 3. Populate event FK from floor_plan.event
        migrations.RunPython(migrate_booth_event, migrations.RunPython.noop),

        # 4. Remove old position / dimension fields
        migrations.RemoveField(model_name='booth', name='floor_plan'),
        migrations.RemoveField(model_name='booth', name='x_percent'),
        migrations.RemoveField(model_name='booth', name='y_percent'),
        migrations.RemoveField(model_name='booth', name='width_meters'),
        migrations.RemoveField(model_name='booth', name='height_meters'),

        # 5. Add grid fields
        migrations.AddField(
            model_name='booth',
            name='grid_x',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='booth',
            name='grid_y',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='booth',
            name='grid_w',
            field=models.PositiveSmallIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='booth',
            name='grid_h',
            field=models.PositiveSmallIntegerField(default=1),
        ),

        # 6. Make event non-nullable
        migrations.AlterField(
            model_name='booth',
            name='event',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='booths',
                to='events.event',
            ),
        ),

        # 7. Restore unique_together on the new event/booth_number pair
        migrations.AlterUniqueTogether(
            name='booth',
            unique_together={('event', 'booth_number')},
        ),

        # 8. Drop the FloorPlan model
        migrations.DeleteModel(name='FloorPlan'),
    ]
