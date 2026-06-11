from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            "UPDATE notifications_notification SET notification_type='SYSTEM' WHERE notification_type='ORG_UPDATE';",
            migrations.RunSQL.noop,
        ),
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(
                choices=[
                    ('APP_UPDATE', 'Application Update'),
                    ('PAY_UPDATE', 'Payment Update'),
                    ('MESSAGE', 'New Message'),
                    ('SYSTEM', 'System'),
                ],
                max_length=20,
            ),
        ),
    ]
