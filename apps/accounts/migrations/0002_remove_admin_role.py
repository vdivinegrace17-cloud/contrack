from django.db import migrations


def reassign_admin_to_organizer(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    User.objects.filter(role='ADMIN').update(role='ORGANIZER', is_staff=True)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(reassign_admin_to_organizer, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=__import__('django.db.models', fromlist=['CharField']).CharField(
                choices=[('ORGANIZER', 'Organizer'), ('MERCHANT', 'Merchant')],
                default='MERCHANT',
                max_length=20,
            ),
        ),
    ]
