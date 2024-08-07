# Generated by Django 2.2.24 on 2021-11-15 11:23

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('astrobin_apps_equipment', '0031_mount_mounteditproposal'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mount',
            name='type',
            field=models.CharField(choices=[('ALTAZIMUTH', 'Alt-Az (altazimuth)'), ('WEDGED_ALTAZIMUTH', 'Wedged Alt-Az'), ('EQUATORIAL', 'Equatorial'), ('GERMAN_EQUATORIAL', 'German equatorial'), ('FORK', 'Fork'), ('DOBSONIAN', 'Dobsonian'), ('PORTABLE_ENGLISH', 'Portable English'), ('BARN_DOOR_TRACKER', 'Star tracker'), ('ALT_ALT', 'Alt-Alt (altitude-altitude)'), ('TRANSIT', 'Transit'), ('HEXAPOD', 'Hexapod'), ('OTHER', 'Other')], max_length=32, verbose_name='Type'),
        ),
        migrations.AlterField(
            model_name='mounteditproposal',
            name='type',
            field=models.CharField(choices=[('ALTAZIMUTH', 'Alt-Az (altazimuth)'), ('WEDGED_ALTAZIMUTH', 'Wedged Alt-Az'), ('EQUATORIAL', 'Equatorial'), ('GERMAN_EQUATORIAL', 'German equatorial'), ('FORK', 'Fork'), ('DOBSONIAN', 'Dobsonian'), ('PORTABLE_ENGLISH', 'Portable English'), ('BARN_DOOR_TRACKER', 'Star tracker'), ('ALT_ALT', 'Alt-Alt (altitude-altitude)'), ('TRANSIT', 'Transit'), ('HEXAPOD', 'Hexapod'), ('OTHER', 'Other')], max_length=32, verbose_name='Type'),
        ),
    ]
