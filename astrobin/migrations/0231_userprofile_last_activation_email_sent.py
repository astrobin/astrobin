# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin', '0230_add_view_count_to_images'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='last_activation_email_sent',
            field=models.DateTimeField(
                blank=True, editable=False, help_text='The time when the last activation email was sent', null=True,
                verbose_name='Last activation email sent'
            ),
        ),
    ]
