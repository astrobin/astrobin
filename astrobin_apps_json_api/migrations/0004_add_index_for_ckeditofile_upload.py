# Generated by Django 2.2.24 on 2023-11-18 18:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin_apps_json_api', '0003_ckeditorfile_thumbnail'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='ckeditorfile',
            index=models.Index(fields=['upload'], name='upload_idx'),
        ),
    ]
