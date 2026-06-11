from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0001_initial'),
        ('events', '0002_swap_org_for_organizer'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Organization',
        ),
    ]
