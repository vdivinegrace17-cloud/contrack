from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0002_swap_org_for_organizer'),
    ]

    operations = [
        migrations.RemoveField(model_name='event', name='latitude'),
        migrations.RemoveField(model_name='event', name='longitude'),
    ]
