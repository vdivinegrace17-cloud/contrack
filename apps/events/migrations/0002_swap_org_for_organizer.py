from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0001_initial'),
        ('accounts', '0002_remove_admin_role'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='organization',
        ),
        migrations.AddField(
            model_name='event',
            name='organizer',
            field=models.ForeignKey(
                blank=True,
                null=True,
                limit_choices_to={'role': 'ORGANIZER'},
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='events',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
